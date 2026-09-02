unit UserScript;

{
  Starfield - Export Planet Atmospheric Resources.pas
  
  Version: 9

  Purpose:
    Export effective planet-level atmospheric inorganic resources by resolving:
      PNDT -> ATMO -> RFDP parent chain -> RDIF reflected Inorganic Resources list

  Tested target:
    xEdit / SF1Edit 4.1.5p

  Output grain:
    One row per PNDT x effective atmospheric IRES resource.

  Output columns:
    SourceFile
    ExtractTimestamp
    PlanetFormID
    PlanetEditorID
    PlanetName
    BodyType
    StarSystemID
    SystemName
    ParentPlanetID
    PlanetID
    AtmosphereFormID
    AtmosphereEditorID
    AtmosphereSourceFile
    AtmosphericResourceCount
    AtmosphericResourceIndex
    ResourceFormID
    ResourceEditorID
    ResourceName
    ResourceSourceFile
    ResourceDefinedByAtmosphereFormID
    ResourceDefinedByAtmosphereEditorID
    ResourceDefinedByAtmosphereSourceFile
    AtmosphereInheritanceDepth

  Important evidence / implementation notes:
    - ATMO records use RFDP - Reflection Parent plus RDIF - Reflection Diff.
    - Creation Kit displays effective inherited values, while xEdit 4.1.5p does not
      currently decode the reflected "Inorganic Resources" property.
    - Known populated local resource lists serialize in RDIF\Diff\Unknown as a
      LIST chunk whose elements are 8-byte reflected form references:
          0D FF FF FF <FormID little-endian>
    - The 32-bit value immediately before the elements is the list element count.
    - A child ATMO with no local resource LIST inherits the parent's effective list.
    - A populated local LIST replaces the inherited list.
    - Vectera provides evidence that a sole zero-count LIST can explicitly clear
      an inherited list. Because xEdit does not expose the reflected property ID,
      that zero-list identification remains the one PROVISIONAL part of this parser.
    - Non-empty LIST chunks are accepted as atmospheric-resource lists only when
      every decoded element resolves to an IRES record.
    - If an RDIF contains ambiguous LIST data, the script reports a warning rather
      than silently inventing a result.

  Run on:
    Selected PNDT records or the PNDT group.

  Output:
    planet-atmospheric-resources.csv
}

var
  sl: TStringList;
  extractTimestamp: string;
  OutPath: string;

function SafeGetEditValue(e: IInterface; const Path: string): string;
var
  x: IInterface;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  x := ElementByPath(e, Path);
  if Assigned(x) then
    Result := GetEditValue(x);
end;

function CsvField(const s: string): string;
begin
  Result := s;

  if (Pos(',', s) > 0) or
     (Pos('"', s) > 0) or
     (Pos(#13, s) > 0) or
     (Pos(#10, s) > 0) then begin
    Result := StringReplace(s, '"', '""', [rfReplaceAll]);
    Result := '"' + Result + '"';
  end;
end;

function ExtractSystemID(const s: string): string;
var
  p: Integer;
begin
  Result := Trim(s);
  p := Pos(' ', Result);
  if p > 0 then
    Result := Copy(Result, 1, p - 1);
end;

function ExtractParenText(const s: string): string;
var
  p1, p2: Integer;
begin
  Result := '';
  p1 := Pos('(', s);
  p2 := Pos(')', s);

  if (p1 > 0) and (p2 > p1) then
    Result := Copy(s, p1 + 1, p2 - p1 - 1);
end;

function GetFullName(e: IInterface): string;
var
  i: Integer;
  comps, comp, compType, fullName: IInterface;
begin
  Result := '';

  if not Assigned(e) then
    Exit;

  { Common direct paths first. }
  Result := SafeGetEditValue(e, 'Body\ANAM - Name');
  if Result <> '' then
    Exit;

  Result := SafeGetEditValue(e, 'FULL - Name');
  if Result <> '' then
    Exit;

  { Fallback: locate TESFullName_Component. }
  comps := ElementByPath(e, 'Base Form Components');
  if not Assigned(comps) then
    Exit;

  for i := 0 to ElementCount(comps) - 1 do begin
    comp := ElementByIndex(comps, i);
    if not Assigned(comp) then
      Continue;

    compType := ElementByPath(comp, 'BFCB - Component Type');
    if not Assigned(compType) then
      Continue;

    if SameText(GetEditValue(compType), 'TESFullName_Component') then begin
      fullName := ElementByPath(comp, 'Component Data - Fullname\FULL - Name');
      if Assigned(fullName) then begin
        Result := GetEditValue(fullName);
        Exit;
      end;
    end;
  end;
end;

function FindFirstLinkedRecordBySignature(e: IInterface; const TargetSig: string): IInterface;
var
  i: Integer;
  child, linked: IInterface;
begin
  Result := nil;

  if not Assigned(e) then
    Exit;

  if ElementCount(e) > 0 then begin
    for i := 0 to ElementCount(e) - 1 do begin
      child := ElementByIndex(e, i);
      Result := FindFirstLinkedRecordBySignature(child, TargetSig);
      if Assigned(Result) then
        Exit;
    end;
    Exit;
  end;

  linked := nil;
  try
    linked := LinksTo(e);
  except
    linked := nil;
  end;

  if not Assigned(linked) then
    Exit;

  if Signature(linked) = TargetSig then
    Result := WinningOverride(linked);
end;

function ResolveFormID(formID: Int64): IInterface; forward;

function ExtractBracketFormID(const s: string): Int64;
var
  p, q: Integer;
  hexText: string;
begin
  Result := -1;

  { Expected xEdit edit-value shape:
      AtmoOrangeBaseDense01 [ATMO:0000288F]
    Do not depend on the EditorID; extract the eight hex digits after "ATMO:".
  }
  p := Pos('[ATMO:', s);
  if p = 0 then
    Exit;

  p := p + Length('[ATMO:');
  q := Pos(']', Copy(s, p, Length(s) - p + 1));
  if q = 0 then
    Exit;

  hexText := Copy(s, p, q - 1);
  if Length(hexText) <> 8 then
    Exit;

  try
    Result := StrToInt64('$' + hexText);
  except
    Result := -1;
  end;
end;

function GetAtmosphereParent(atmo: IInterface): IInterface;
var
  x, linked: IInterface;
  parentText: string;
  parentFormID: Int64;
begin
  Result := nil;

  if not Assigned(atmo) then
    Exit;

  {
    RFDP is a real subrecord signature.  In xEdit 4.1.5p the display tree
    labels it "RFDP - Reflection Parent", but that display label is not
    reliably addressable through ElementByPath().  Prefer signature lookup.
  }
  x := ElementBySignature(atmo, 'RFDP');

  if not Assigned(x) then
    x := ElementByPath(atmo, 'RFDP - Reflection Parent');

  if not Assigned(x) then begin
    {
      No RFDP is normal for root/default ATMO records.  The caller will
      treat the current ATMO as the inheritance root and decode its REFL data.
    }
    Exit;
  end;

  { First use the normal xEdit link resolver when available. }
  linked := nil;
  try
    linked := LinksTo(x);
  except
    linked := nil;
  end;

  if Assigned(linked) and (Signature(linked) = 'ATMO') then begin
    Result := WinningOverride(linked);
    Exit;
  end;

  {
    Starfield reflection-parent fields are exposed by xEdit 4.1.5p as a
    leaf subrecord whose edit value looks like:
        AtmoOrangeBaseDense01 [ATMO:0000288F]
    LinksTo() does not reliably resolve this RFDP leaf, so fall back to
    extracting the FormID from the displayed value and resolving it explicitly.
  }
  parentText := GetEditValue(x);
  parentFormID := ExtractBracketFormID(parentText);

  if parentFormID < 0 then begin
    if Trim(parentText) <> '' then
      AddMessage(
        'WARNING: unable to parse RFDP parent for ' +
        EditorID(atmo) + ' [' + IntToHex(FixedFormID(atmo), 8) +
        '] from value "' + parentText + '".'
      );
    Exit;
  end;

  {
    RFDP's displayed FormID is a fixed/local FormID in the owning file's
    master context. Resolve it through the child ATMO's own file rather than
    scanning unrelated loaded plugins for the same local FormID.
  }
  linked := nil;
  try
    linked := RecordByFormID(GetFile(atmo), parentFormID, True);
  except
    linked := nil;
  end;

  if Assigned(linked) and (Signature(linked) = 'ATMO') then begin
    linked := WinningOverride(linked);

    Result := linked;
    Exit;
  end;

  AddMessage(
    'WARNING: RFDP parent FormID ' + IntToHex(parentFormID, 8) +
    ' for ' + EditorID(atmo) + ' [' + IntToHex(FixedFormID(atmo), 8) +
    '] could not be resolved through ' + GetFileName(GetFile(atmo)) +
    ' to an ATMO record.'
  );
end;

function NormalizeHex(const s: string): string;
var
  i: Integer;
  c: Char;
begin
  Result := '';

  for i := 1 to Length(s) do begin
    c := UpCase(s[i]);
    if ((c >= '0') and (c <= '9')) or
       ((c >= 'A') and (c <= 'F')) then
      Result := Result + c;
  end;
end;

function HexByteAt(const h: string; ByteOffset: Integer): Integer;
var
  p: Integer;
  pair: string;
begin
  Result := -1;

  p := ByteOffset * 2 + 1;
  if (p < 1) or (p + 1 > Length(h)) then
    Exit;

  pair := Copy(h, p, 2);

  try
    Result := StrToInt('$' + pair);
  except
    Result := -1;
  end;
end;

function UInt32LEAt(const h: string; ByteOffset: Integer): Int64;
var
  b0, b1, b2, b3: Integer;
begin
  Result := 0;

  b0 := HexByteAt(h, ByteOffset);
  b1 := HexByteAt(h, ByteOffset + 1);
  b2 := HexByteAt(h, ByteOffset + 2);
  b3 := HexByteAt(h, ByteOffset + 3);

  if (b0 < 0) or (b1 < 0) or (b2 < 0) or (b3 < 0) then
    Exit;

  Result :=
    b0 or
    (b1 shl 8) or
    (b2 shl 16) or
    (b3 shl 24);
end;

function ResolveFormID(formID: Int64): IInterface;
var
  i: Integer;
  f, r: IInterface;
begin
  Result := nil;

  { Search from highest-priority loaded file downward. }
  for i := FileCount - 1 downto 0 do begin
    f := FileByIndex(i);
    if not Assigned(f) then
      Continue;

    r := nil;
    try
      r := RecordByFormID(f, formID, True);
    except
      r := nil;
    end;

    if Assigned(r) then begin
      Result := WinningOverride(r);
      Exit;
    end;
  end;
end;

function IsListMarkerAt(const h: string; ByteOffset: Integer): Boolean;
begin
  Result :=
    (HexByteAt(h, ByteOffset)     = $4C) and
    (HexByteAt(h, ByteOffset + 1) = $49) and
    (HexByteAt(h, ByteOffset + 2) = $53) and
    (HexByteAt(h, ByteOffset + 3) = $54);
end;

function ParseIRESListAt(
  const h: string;
  ListOffset: Integer;
  resources: TStringList
): Boolean;
var
  payloadSize, count: Int64;
  i, itemOffset: Integer;
  formID: Int64;
  r: IInterface;
  tag0, tag1, tag2, tag3: Integer;
begin
  Result := False;
  resources.Clear;

  if not IsListMarkerAt(h, ListOffset) then
    Exit;

  payloadSize := UInt32LEAt(h, ListOffset + 4);
  count := UInt32LEAt(h, ListOffset + 12);

  { Known encoding has 8 bytes of list header plus 8 bytes per element. }
  if payloadSize <> (8 + count * 8) then
    Exit;

  if count = 0 then begin
    Result := True;
    Exit;
  end;

  for i := 0 to count - 1 do begin
    itemOffset := ListOffset + 16 + i * 8;

    tag0 := HexByteAt(h, itemOffset);
    tag1 := HexByteAt(h, itemOffset + 1);
    tag2 := HexByteAt(h, itemOffset + 2);
    tag3 := HexByteAt(h, itemOffset + 3);

    { Reflected form-reference marker observed in ATMO resource lists. }
    if (tag0 <> $0D) or (tag1 <> $FF) or
       (tag2 <> $FF) or (tag3 <> $FF) then begin
      resources.Clear;
      Exit;
    end;

    formID := UInt32LEAt(h, itemOffset + 4);
    r := ResolveFormID(formID);

    if not Assigned(r) or (Signature(r) <> 'IRES') then begin
      resources.Clear;
      Exit;
    end;

    resources.Add(IntToHex(formID, 8));
  end;

  Result := True;
end;

function TryGetLocalAtmosphericResourceOverride(
  atmo: IInterface;
  resources: TStringList;
  var usedProvisionalEmptyListRule: Boolean
): Boolean;
var
  raw, h: string;
  byteCount, p: Integer;
  listCount, validNonEmptyIRESLists, zeroLists: Integer;
  temp, chosen: TStringList;
begin
  Result := False;
  usedProvisionalEmptyListRule := False;
  resources.Clear;

  raw := SafeGetEditValue(atmo, 'RDIF - Reflection Diff\Diff\Unknown');
  if raw = '' then
    Exit;

  h := NormalizeHex(raw);
  byteCount := Length(h) div 2;

  listCount := 0;
  validNonEmptyIRESLists := 0;
  zeroLists := 0;

  temp := TStringList.Create;
  chosen := TStringList.Create;
  try
    p := 0;
    while p <= byteCount - 16 do begin
      if IsListMarkerAt(h, p) then begin
        Inc(listCount);

        temp.Clear;
        if ParseIRESListAt(h, p, temp) then begin
          if temp.Count = 0 then
            Inc(zeroLists)
          else begin
            Inc(validNonEmptyIRESLists);
            chosen.Assign(temp);
          end;
        end;
      end;

      Inc(p);
    end;

    if validNonEmptyIRESLists = 1 then begin
      resources.Assign(chosen);
      Result := True;
      Exit;
    end;

    if validNonEmptyIRESLists > 1 then begin
      AddMessage(
        'WARNING: multiple IRES LIST chunks in ' +
        EditorID(atmo) + ' [' + IntToHex(FixedFormID(atmo), 8) +
        ']; atmospheric resource override is ambiguous.'
      );
      Exit;
    end;

    {
      PROVISIONAL rule:
        Vectera demonstrates a child ATMO whose CK Inorganic Resources value
        is empty and whose RDIF contains a single zero-count LIST.
        Until the reflected property identifier is decoded, accept a sole
        zero-count LIST as an explicit atmospheric-resource clear.
    }
    if (listCount = 1) and (zeroLists = 1) then begin
      resources.Clear;
      Result := True;
      usedProvisionalEmptyListRule := True;

      Exit;
    end;
  finally
    temp.Free;
    chosen.Free;
  end;
end;


function TryGetRootAtmosphericResources(
  atmo: IInterface;
  resources: TStringList
): Boolean;
var
  refl, objectData: IInterface;
  raw, h: string;
  byteCount, p: Integer;
  validNonEmptyIRESLists, zeroLists: Integer;
  temp, chosen: TStringList;
begin
  Result := False;
  resources.Clear;

  {
    Root/default ATMO records have no RFDP parent.  Their complete reflected
    object is stored in REFL rather than RDIF.  Known examples
    AtmoDefaultMedium and AtmoDefaultDense contain the atmospheric-resource
    LIST in:
        REFL - Reflection\Object Data\Unknown
  }

  refl := ElementBySignature(atmo, 'REFL');
  if not Assigned(refl) then
    refl := ElementByPath(atmo, 'REFL - Reflection');

  if not Assigned(refl) then
    Exit;

  objectData := ElementByPath(refl, 'Object Data\Unknown');
  if not Assigned(objectData) then
    Exit;

  raw := GetEditValue(objectData);
  if raw = '' then
    Exit;

  h := NormalizeHex(raw);
  byteCount := Length(h) div 2;

  validNonEmptyIRESLists := 0;
  zeroLists := 0;

  temp := TStringList.Create;
  chosen := TStringList.Create;
  try
    p := 0;
    while p <= byteCount - 16 do begin
      if IsListMarkerAt(h, p) then begin
        temp.Clear;

        if ParseIRESListAt(h, p, temp) then begin
          if temp.Count = 0 then
            Inc(zeroLists)
          else begin
            Inc(validNonEmptyIRESLists);
            chosen.Assign(temp);
          end;
        end;
      end;

      Inc(p);
    end;

    if validNonEmptyIRESLists = 1 then begin
      resources.Assign(chosen);

      Result := True;
      Exit;
    end;

    if validNonEmptyIRESLists > 1 then begin
      AddMessage(
        'WARNING: multiple IRES LIST chunks in root REFL for ' +
        EditorID(atmo) + ' [' + IntToHex(FixedFormID(atmo), 8) +
        ']; atmospheric resource value is ambiguous.'
      );
      Exit;
    end;

    {
      A root REFL with no valid IRES list is treated as an effective empty
      atmospheric-resource list.  Unlike child RDIF zero-list detection,
      this does not require guessing override semantics because there is no
      parent value to inherit.
    }
    resources.Clear;
    Result := True;
  finally
    temp.Free;
    chosen.Free;
  end;
end;

function ResolveAtmosphericResources(
  atmo: IInterface;
  resources: TStringList;
  var definedByAtmo: IInterface;
  var inheritanceDepth: Integer
): Boolean;
var
  current, parent: IInterface;
  localResources: TStringList;
  depth: Integer;
  usedProvisionalEmptyListRule: Boolean;
begin
  Result := False;
  resources.Clear;
  definedByAtmo := nil;
  inheritanceDepth := -1;

  current := atmo;
  depth := 0;

  localResources := TStringList.Create;
  try
    while Assigned(current) and (depth <= 32) do begin
      localResources.Clear;
      usedProvisionalEmptyListRule := False;

      if TryGetLocalAtmosphericResourceOverride(
        current,
        localResources,
        usedProvisionalEmptyListRule
      ) then begin
        resources.Assign(localResources);
        definedByAtmo := current;
        inheritanceDepth := depth;
        Result := True;
        Exit;
      end;

      parent := GetAtmosphereParent(current);
      if not Assigned(parent) then begin
        {
          Root/default ATMO: resolve its complete reflected object from REFL.
          Child records use RDIF differences; root records have no parent and
          therefore serialize the base value in REFL.
        }
        if TryGetRootAtmosphericResources(current, localResources) then begin
          resources.Assign(localResources);
          definedByAtmo := current;
          inheritanceDepth := depth;
          Result := True;
          Exit;
        end;

        AddMessage(
          'WARNING: unable to decode root REFL atmospheric resources for ' +
          EditorID(current) + ' [' + IntToHex(FixedFormID(current), 8) + '].'
        );
        Exit;
      end;

      current := parent;
      Inc(depth);
    end;

    if depth > 32 then
      AddMessage(
        'WARNING: ATMO inheritance depth exceeded 32 while resolving ' +
        EditorID(atmo) + ' [' + IntToHex(FixedFormID(atmo), 8) + '].'
      );
  finally
    localResources.Free;
  end;
end;

function Initialize: Integer;
begin
  Result := 0;

  sl := TStringList.Create;

  extractTimestamp := FormatDateTime('yyyy-mm-dd hh:nn:ss', Now);

  sl.Add(
    'SourceFile' + ',' +
    'ExtractTimestamp' + ',' +
    'PlanetFormID' + ',' +
    'PlanetEditorID' + ',' +
    'PlanetName' + ',' +
    'BodyType' + ',' +
    'StarSystemID' + ',' +
    'SystemName' + ',' +
    'ParentPlanetID' + ',' +
    'PlanetID' + ',' +
    'AtmosphereFormID' + ',' +
    'AtmosphereEditorID' + ',' +
    'AtmosphereSourceFile' + ',' +
    'AtmosphericResourceCount' + ',' +
    'AtmosphericResourceIndex' + ',' +
    'ResourceFormID' + ',' +
    'ResourceEditorID' + ',' +
    'ResourceName' + ',' +
    'ResourceSourceFile' + ',' +
    'ResourceDefinedByAtmosphereFormID' + ',' +
    'ResourceDefinedByAtmosphereEditorID' + ',' +
    'ResourceDefinedByAtmosphereSourceFile' + ',' +
    'AtmosphereInheritanceDepth'
  );

  OutPath := ScriptsPath + 'planet-atmospheric-resources.csv';

end;

function Process(e: IInterface): Integer;
var
  sig, sourceFile, planetFormID, planetEditorID: string;
  planetName, bodyType: string;
  systemRaw, systemID, systemName: string;
  parentPlanetID, planetID: string;

  atmo, definedByAtmo, resourceRecord: IInterface;
  atmoFormID, atmoEditorID, atmoSourceFile: string;
  definedByFormID, definedByEditorID, definedBySourceFile: string;
  resourceFormID, resourceEditorID, resourceName, resourceSourceFile: string;

  resources: TStringList;
  inheritanceDepth, i: Integer;
begin
  Result := 0;

  if not Assigned(e) then
    Exit;

  sig := Signature(e);
  if sig <> 'PNDT' then
    Exit;

  sourceFile := GetFileName(GetFile(e));
  planetFormID := IntToHex(FixedFormID(e), 8);
  planetEditorID := EditorID(e);

  planetName := GetFullName(e);
  bodyType := SafeGetEditValue(e, 'Body\CNAM - Body type');

  systemRaw := SafeGetEditValue(e, 'Body\GNAM - Galaxy Data\Star System ID');
  systemID := ExtractSystemID(systemRaw);
  systemName := ExtractParenText(systemRaw);

  parentPlanetID := SafeGetEditValue(e, 'Body\GNAM - Galaxy Data\Parent Planet ID');
  planetID := SafeGetEditValue(e, 'Body\GNAM - Galaxy Data\Planet ID');

  {
    xEdit's displayed PNDT path for the atmosphere reference may change as
    Starfield definitions improve. Find the linked ATMO structurally rather
    than hard-coding one currently-undecoded PNDT path.
  }
  atmo := FindFirstLinkedRecordBySignature(e, 'ATMO');
  if not Assigned(atmo) then
    Exit;

  atmoFormID := IntToHex(FixedFormID(atmo), 8);
  atmoEditorID := EditorID(atmo);
  atmoSourceFile := GetFileName(GetFile(atmo));

  resources := TStringList.Create;
  try
    if not ResolveAtmosphericResources(
      atmo,
      resources,
      definedByAtmo,
      inheritanceDepth
    ) then begin
      AddMessage(
        'WARNING: unable to resolve atmospheric resources for planet ' +
        planetEditorID + ' [' + planetFormID + '] via ' +
        atmoEditorID + ' [' + atmoFormID + '].'
      );
      Exit;
    end;

    { Normalized fact extract: planets with zero effective atmospheric
      resources produce no data rows. }
    if resources.Count = 0 then
      Exit;

    definedByFormID := '';
    definedByEditorID := '';
    definedBySourceFile := '';

    if Assigned(definedByAtmo) then begin
      definedByFormID := IntToHex(FixedFormID(definedByAtmo), 8);
      definedByEditorID := EditorID(definedByAtmo);
      definedBySourceFile := GetFileName(GetFile(definedByAtmo));
    end;

    for i := 0 to resources.Count - 1 do begin
      resourceFormID := resources[i];
      resourceRecord := ResolveFormID(StrToInt64('$' + resourceFormID));

      resourceEditorID := '';
      resourceName := '';
      resourceSourceFile := '';

      if Assigned(resourceRecord) then begin
        resourceEditorID := EditorID(resourceRecord);
        resourceName := GetFullName(resourceRecord);
        resourceSourceFile := GetFileName(GetFile(resourceRecord));
      end;

      sl.Add(
        CsvField(sourceFile) + ',' +
        CsvField(extractTimestamp) + ',' +
        CsvField(planetFormID) + ',' +
        CsvField(planetEditorID) + ',' +
        CsvField(planetName) + ',' +
        CsvField(bodyType) + ',' +
        CsvField(systemID) + ',' +
        CsvField(systemName) + ',' +
        CsvField(parentPlanetID) + ',' +
        CsvField(planetID) + ',' +
        CsvField(atmoFormID) + ',' +
        CsvField(atmoEditorID) + ',' +
        CsvField(atmoSourceFile) + ',' +
        CsvField(IntToStr(resources.Count)) + ',' +
        CsvField(IntToStr(i)) + ',' +
        CsvField(resourceFormID) + ',' +
        CsvField(resourceEditorID) + ',' +
        CsvField(resourceName) + ',' +
        CsvField(resourceSourceFile) + ',' +
        CsvField(definedByFormID) + ',' +
        CsvField(definedByEditorID) + ',' +
        CsvField(definedBySourceFile) + ',' +
        CsvField(IntToStr(inheritanceDepth))
      );
    end;
  finally
    resources.Free;
  end;
end;

function Finalize: Integer;
begin
  Result := 0;

  try
    sl.SaveToFile(OutPath);
  finally
    sl.Free;
  end;
end;

end.
