unit UserScript;

{
  Starfield_ExportPlanetResourceGeneration_v5.pas

  Purpose:
    Export the PNDT -> BIOM -> RSGD -> IRES resource-generation inputs
    needed for analysis of Starfield's planetary resource allocation.

  Output grain:
    PNDT x biome entry x distinct referenced RSGD x RSGD resource entry

  RSGD provenance:
    - PNDT only                         -> RSGDSource = PNDT
    - BIOM only                         -> RSGDSource = BIOM
    - PNDT and BIOM reference same form -> RSGDSource = PNDT+BIOM
    - PNDT and BIOM reference different forms:
        emit both independently with PNDT / BIOM provenance

  Deduplication:
    Only the same referenced RSGD record is deduplicated. Distinct RSGD
    records are never deduplicated merely because their contents match.

  Intended target:
    xEdit / SF1Edit 4.1.5p

  Output:
    PlanetResourceGeneration.csv

  Notes:
    - Read-only. The script does not modify records.
    - Intended for one or more selected PNDT records, or application to
      the PNDT group.
    - BiomeIndex preserves PNDT PPBD order.
    - RSGDResourceIndex preserves RSGD Resources array order.
    - Cell generation probabilities are deliberately excluded.
    - IRES child relationships are deliberately excluded; they belong in
      the separate Starfield_IRES_Hierarchy dataset.
}

var
  sl: TStringList;
  OutPath: string;
  ExtractTimestamp: string;

function CsvEscape(const s: string): string;
var
  t: string;
begin
  t := StringReplace(s, '"', '""', [rfReplaceAll]);
  Result := '"' + t + '"';
end;

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

function SafeEditorID(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  try
    Result := EditorID(e);
  except
    Result := '';
  end;
end;

function SafeFixedFormID(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  try
    Result := IntToHex(FixedFormID(e), 8);
  except
    Result := '';
  end;
end;


function SafeSourceFile(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  try
    Result := GetFileName(GetFile(e));
  except
    Result := '';
  end;
end;

function UInt32Decimal(const s: string): string;
var
  v: Int64;
begin
  Result := '';

  if Trim(s) = '' then
    Exit;

  try
    v := StrToInt64(Trim(s));

    {
      xEdit may expose a 32-bit field as a signed decimal value.
      Convert negative signed representations into the equivalent
      unsigned 32-bit range without changing the underlying bits.
    }
    if v < 0 then
      v := v + 4294967296;

    if (v < 0) or (v > 4294967295) then begin
      AddMessage('Resource Creation Seed outside UInt32 range: ' + s);
      Exit;
    end;

    Result := IntToStr(v);
  except
    AddMessage('Unable to parse Resource Creation Seed: ' + s);
    Result := '';
  end;
end;

function RecordKey(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  try
    Result := GetFileName(GetFile(e)) + ':' + SafeFixedFormID(e);
  except
    Result := SafeFixedFormID(e);
  end;
end;

function SameRecord(a, b: IInterface): Boolean;
begin
  Result := False;

  if (not Assigned(a)) or (not Assigned(b)) then
    Exit;

  Result := SameText(RecordKey(a), RecordKey(b));
end;

function ResolveReference(refElement: IInterface; const ExpectedSignature: string): IInterface;
var
  linked: IInterface;
begin
  Result := nil;

  if not Assigned(refElement) then
    Exit;

  linked := nil;
  try
    linked := LinksTo(refElement);
  except
    linked := nil;
  end;

  if not Assigned(linked) then
    Exit;

  if (ExpectedSignature <> '') and
     (not SameText(Signature(linked), ExpectedSignature)) then
    Exit;

  Result := linked;
end;

function GetPlanetFullName(e: IInterface): string;
var
  i: Integer;
  comps, comp, compType, fullName: IInterface;
begin
  Result := '';

  { Primary PNDT name location. }
  Result := SafeGetEditValue(e, 'Body\ANAM - Name');
  if Result <> '' then
    Exit;

  { Fallback used by some Starfield records. }
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

function GetRecordFullName(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  Result := SafeGetEditValue(e, 'FULL - Name');

  if Result = '' then
    Result := SafeGetEditValue(e, 'FULL');
end;

function GetFirstUnknownRaw(biomeEntry: IInterface): string;
var
  i: Integer;
  child: IInterface;
  n: string;
begin
  Result := '';

  if not Assigned(biomeEntry) then
    Exit;

  {
    PNDT PPBD entries contain more than one "Unknown" field.
    The specification requires the first one: Unknown #0.
    Iterate in stored order and take the first direct child whose name
    begins with "Unknown".
  }
  for i := 0 to ElementCount(biomeEntry) - 1 do begin
    child := ElementByIndex(biomeEntry, i);
    if not Assigned(child) then
      Continue;

    n := Name(child);

    if Pos('Unknown', n) = 1 then begin
      Result := GetEditValue(child);
      Exit;
    end;
  end;
end;

function HexDigitValue(c: Char): Integer;
var
  p: Integer;
  s: string;
begin
  Result := -1;
  s := UpperCase(c);
  p := Pos(s, '0123456789ABCDEF');
  if p > 0 then
    Result := p - 1;
end;

function ParseHexByte(const s: string; p: Integer): Integer;
var
  hi, lo: Integer;
begin
  Result := -1;

  if (p < 1) or (p + 1 > Length(s)) then
    Exit;

  hi := HexDigitValue(s[p]);
  lo := HexDigitValue(s[p + 1]);

  if (hi < 0) or (lo < 0) then
    Exit;

  Result := hi * 16 + lo;
end;

function DecodeLittleEndianUInt32(const raw: string): string;
var
  i, d: Integer;
  compact: string;
  b0, b1, b2, b3: Integer;
  v: Int64;
begin
  Result := '';
  compact := '';

  {
    Keep only hex digits so values such as
      F6 85 80 8D
    become
      F685808D
  }
  for i := 1 to Length(raw) do begin
    d := HexDigitValue(raw[i]);
    if d >= 0 then
      compact := compact + raw[i];
  end;

  if Length(compact) < 8 then
    Exit;

  b0 := ParseHexByte(compact, 1);
  b1 := ParseHexByte(compact, 3);
  b2 := ParseHexByte(compact, 5);
  b3 := ParseHexByte(compact, 7);

  if (b0 < 0) or (b1 < 0) or (b2 < 0) or (b3 < 0) then
    Exit;

  { Build as Int64 to preserve the full unsigned 32-bit range. }
  v := b3;
  v := v * 256 + b2;
  v := v * 256 + b1;
  v := v * 256 + b0;

  Result := IntToStr(v);
end;

function FindRSGDReferenceRecursive(e: IInterface): IInterface;
var
  i: Integer;
  child, linked: IInterface;
begin
  Result := nil;

  if not Assigned(e) then
    Exit;

  {
    First test the current element itself. LinksTo() returns nil for
    ordinary containers/values, but resolves FormID/reference elements.
    We accept only references whose linked main record is actually RSGD.
  }
  linked := ResolveReference(e, 'RSGD');
  if Assigned(linked) then begin
    Result := linked;
    Exit;
  end;

  {
    Then traverse the BIOM's own element tree. We do not recurse through
    linked records, so this cannot wander into external record graphs.
  }
  for i := 0 to ElementCount(e) - 1 do begin
    child := ElementByIndex(e, i);
    if not Assigned(child) then
      Continue;

    Result := FindRSGDReferenceRecursive(child);
    if Assigned(Result) then
      Exit;
  end;
end;

function FindBIOMRSGD(biomRec: IInterface): IInterface;
var
  refElement, linked: IInterface;
begin
  Result := nil;

  if not Assigned(biomRec) then
    Exit;

  {
    Try known/likely display paths first.
  }
  refElement := ElementByPath(biomRec, 'RNAM - Resource Generation');
  if not Assigned(refElement) then
    refElement := ElementByPath(biomRec, 'Resource Generation (sorted)');
  if not Assigned(refElement) then
    refElement := ElementByPath(biomRec, 'Resource Generation');

  linked := ResolveReference(refElement, 'RSGD');
  if Assigned(linked) then begin
    Result := linked;
    Exit;
  end;

  {
    The BIOM RSGD reference is not necessarily a direct child in xEdit's
    displayed structure. Fall back to recursively scanning the BIOM's
    element tree for a reference that resolves to an RSGD record.
  }
  Result := FindRSGDReferenceRecursive(biomRec);
end;

function GetIRESRarity(iresRec: IInterface): string;
begin
  Result := '';
  if not Assigned(iresRec) then
    Exit;

  Result := SafeGetEditValue(iresRec, 'SNAM - Rarity');
end;

function GetBiomeChanceValue(resourceEntry: IInterface;
  const RarityName: string): string;
var
  path: string;
begin
  Result := '';

  if not Assigned(resourceEntry) then
    Exit;

  {
    Common uses "Chance to Appear".
    All descendant/special/everywhere categories use "Chance per Node".
  }
  if SameText(RarityName, 'Common') then
    path := 'DNAM - Generation Data\Biome\Common\Chance to Appear'
  else
    path := 'DNAM - Generation Data\Biome\' +
            RarityName + '\Chance per Node';

  Result := SafeGetEditValue(resourceEntry, path);
end;

procedure EmitRSGDRows(
  planetRec: IInterface;
  const SourceFile: string;
  const PlanetFormID: string;
  const PlanetEditorID: string;
  const PlanetName: string;
  const ResourceCreationSeed: string;
  BiomeIndex: Integer;
  biomeRec: IInterface;
  const BiomeChance: string;
  const BiomeUnknown0Raw: string;
  const BiomeUnknown0UInt32: string;
  const RSGDSource: string;
  rsgdRec: IInterface
);
var
  resources, resourceEntry, resourceRef, resourceRec: IInterface;
  i: Integer;
  resourceFormID, resourceEditorID, resourceName, resourceRarity: string;
  biomeCommonChance, biomeUncommonChance, biomeRareChance: string;
  biomeExoticChance, biomeUniqueChance, biomeSpecialChance: string;
  biomeEverywhereChance: string;
  rsgdFormID, rsgdEditorID, rsgdSourceFile: string;
  biomeSourceFile, resourceSourceFile: string;
begin
  if not Assigned(rsgdRec) then
    Exit;

  resources := ElementByPath(rsgdRec, 'Resources');
  if not Assigned(resources) then begin
    AddMessage(
      'RSGD has no Resources array: ' +
      SafeEditorID(rsgdRec) + ' [' + SafeFixedFormID(rsgdRec) + ']'
    );
    Exit;
  end;

  rsgdFormID := SafeFixedFormID(rsgdRec);
  rsgdEditorID := SafeEditorID(rsgdRec);
  rsgdSourceFile := SafeSourceFile(rsgdRec);
  biomeSourceFile := SafeSourceFile(biomeRec);

  for i := 0 to ElementCount(resources) - 1 do begin
    resourceEntry := ElementByIndex(resources, i);
    if not Assigned(resourceEntry) then
      Continue;

    resourceRef := ElementByPath(resourceEntry, 'RNAM - Resource');
    resourceRec := ResolveReference(resourceRef, 'IRES');

    resourceFormID := '';
    resourceEditorID := '';
    resourceName := '';
    resourceRarity := '';
    resourceSourceFile := '';

    if Assigned(resourceRec) then begin
      resourceFormID := SafeFixedFormID(resourceRec);
      resourceEditorID := SafeEditorID(resourceRec);
      resourceName := GetRecordFullName(resourceRec);
      resourceRarity := GetIRESRarity(resourceRec);
      resourceSourceFile := SafeSourceFile(resourceRec);
    end else if Assigned(resourceRef) then begin
      {
        Preserve the visible reference value if resolution unexpectedly
        fails only through the diagnostic log; identity columns remain
        blank rather than inventing a parsed FormID.
      }
      AddMessage(
        'Unable to resolve IRES reference: ' +
        GetEditValue(resourceRef) +
        ' in RSGD ' + rsgdEditorID
      );
    end;

    biomeCommonChance := GetBiomeChanceValue(resourceEntry, 'Common');
    biomeUncommonChance := GetBiomeChanceValue(resourceEntry, 'Uncommon');
    biomeRareChance := GetBiomeChanceValue(resourceEntry, 'Rare');
    biomeExoticChance := GetBiomeChanceValue(resourceEntry, 'Exotic');
    biomeUniqueChance := GetBiomeChanceValue(resourceEntry, 'Unique');
    biomeSpecialChance := GetBiomeChanceValue(resourceEntry, 'Special');
    biomeEverywhereChance := GetBiomeChanceValue(resourceEntry, 'Everywhere');

    sl.Add(
      CsvEscape(SourceFile) + ',' +
      CsvEscape(ExtractTimestamp) + ',' +
      CsvEscape(PlanetFormID) + ',' +
      CsvEscape(PlanetEditorID) + ',' +
      CsvEscape(PlanetName) + ',' +
      CsvEscape(ResourceCreationSeed) + ',' +

      CsvEscape(IntToStr(BiomeIndex)) + ',' +
      CsvEscape(SafeFixedFormID(biomeRec)) + ',' +
      CsvEscape(SafeEditorID(biomeRec)) + ',' +
      CsvEscape(GetRecordFullName(biomeRec)) + ',' +
      CsvEscape(biomeSourceFile) + ',' +
      CsvEscape(BiomeChance) + ',' +
      CsvEscape(BiomeUnknown0Raw) + ',' +
      CsvEscape(BiomeUnknown0UInt32) + ',' +

      CsvEscape(RSGDSource) + ',' +
      CsvEscape(rsgdFormID) + ',' +
      CsvEscape(rsgdEditorID) + ',' +
      CsvEscape(rsgdSourceFile) + ',' +

      CsvEscape(IntToStr(i)) + ',' +
      CsvEscape(resourceFormID) + ',' +
      CsvEscape(resourceEditorID) + ',' +
      CsvEscape(resourceName) + ',' +
      CsvEscape(resourceRarity) + ',' +
      CsvEscape(resourceSourceFile) + ',' +

      CsvEscape(biomeCommonChance) + ',' +
      CsvEscape(biomeUncommonChance) + ',' +
      CsvEscape(biomeRareChance) + ',' +
      CsvEscape(biomeExoticChance) + ',' +
      CsvEscape(biomeUniqueChance) + ',' +
      CsvEscape(biomeSpecialChance) + ',' +
      CsvEscape(biomeEverywhereChance)
    );
  end;
end;

function Initialize: Integer;
begin
  Result := 0;

  sl := TStringList.Create;

  { Capture one local timestamp for the entire extract. }
  ExtractTimestamp := FormatDateTime('yyyy-mm-dd hh:nn:ss', Now);

  sl.Add(
    'SourceFile,' +
    'ExtractTimestamp,' +

    'PlanetFormID,' +
    'PlanetEditorID,' +
    'PlanetName,' +
    'ResourceCreationSeed,' +

    'BiomeIndex,' +
    'BiomeFormID,' +
    'BiomeEditorID,' +
    'BiomeName,' +
    'BiomeSourceFile,' +
    'BiomeChance,' +
    'BiomeUnknown0Raw,' +
    'BiomeUnknown0UInt32,' +

    'RSGDSource,' +
    'RSGDFormID,' +
    'RSGDEditorID,' +
    'RSGDSourceFile,' +

    'RSGDResourceIndex,' +
    'ResourceFormID,' +
    'ResourceEditorID,' +
    'ResourceName,' +
    'ResourceRarity,' +
    'ResourceSourceFile,' +

    'BiomeCommonChance,' +
    'BiomeUncommonChance,' +
    'BiomeRareChance,' +
    'BiomeExoticChance,' +
    'BiomeUniqueChance,' +
    'BiomeSpecialChance,' +
    'BiomeEverywhereChance'
  );

  OutPath := ScriptsPath + 'PlanetResourceGeneration.csv';

  AddMessage('Planet resource-generation export started.');
end;

function Process(e: IInterface): Integer;
var
  biomes, biomeEntry, biomeRef, biomeRec: IInterface;
  pndtRSGDRef, pndtRSGD, biomRSGD: IInterface;
  i: Integer;
  sourceFile, planetFormID, planetEditorID, planetName: string;
  resourceCreationSeed: string;
  biomeChance, biomeUnknown0Raw, biomeUnknown0UInt32: string;
begin
  Result := 0;

  if not Assigned(e) then
    Exit;

  if ElementType(e) <> etMainRecord then
    Exit;

  if Signature(e) <> 'PNDT' then
    Exit;

  sourceFile := GetFileName(GetFile(e));
  planetFormID := SafeFixedFormID(e);
  planetEditorID := SafeEditorID(e);
  planetName := GetPlanetFullName(e);
  resourceCreationSeed := UInt32Decimal(
    SafeGetEditValue(e, 'RSCS - Resource Creation Seed')
  );

  biomes := ElementByPath(e, 'Biomes');
  if not Assigned(biomes) then begin
    AddMessage(
      'PNDT has no Biomes array: ' +
      planetEditorID + ' [' + planetFormID + ']'
    );
    Exit;
  end;

  for i := 0 to ElementCount(biomes) - 1 do begin
    biomeEntry := ElementByIndex(biomes, i);
    if not Assigned(biomeEntry) then
      Continue;

    biomeRef := ElementByPath(biomeEntry, 'Biome');
    biomeRec := ResolveReference(biomeRef, 'BIOM');

    if not Assigned(biomeRec) then begin
      AddMessage(
        'Unable to resolve BIOM for ' +
        planetEditorID + ', biome index ' + IntToStr(i)
      );
      Continue;
    end;

    biomeChance := SafeGetEditValue(biomeEntry, 'Chance');
    biomeUnknown0Raw := GetFirstUnknownRaw(biomeEntry);
    biomeUnknown0UInt32 := DecodeLittleEndianUInt32(biomeUnknown0Raw);

    { PNDT per-biome RSGD override, if present. }
    pndtRSGDRef := ElementByPath(biomeEntry, 'Resource Generation');
    pndtRSGD := ResolveReference(pndtRSGDRef, 'RSGD');

    { BIOM normal RSGD reference. }
    biomRSGD := FindBIOMRSGD(biomeRec);

    if Assigned(pndtRSGD) and Assigned(biomRSGD) then begin
      if SameRecord(pndtRSGD, biomRSGD) then begin
        EmitRSGDRows(
          e,
          sourceFile,
          planetFormID,
          planetEditorID,
          planetName,
          resourceCreationSeed,
          i,
          biomeRec,
          biomeChance,
          biomeUnknown0Raw,
          biomeUnknown0UInt32,
          'PNDT+BIOM',
          pndtRSGD
        );
      end else begin
        EmitRSGDRows(
          e,
          sourceFile,
          planetFormID,
          planetEditorID,
          planetName,
          resourceCreationSeed,
          i,
          biomeRec,
          biomeChance,
          biomeUnknown0Raw,
          biomeUnknown0UInt32,
          'PNDT',
          pndtRSGD
        );

        EmitRSGDRows(
          e,
          sourceFile,
          planetFormID,
          planetEditorID,
          planetName,
          resourceCreationSeed,
          i,
          biomeRec,
          biomeChance,
          biomeUnknown0Raw,
          biomeUnknown0UInt32,
          'BIOM',
          biomRSGD
        );
      end;
    end else if Assigned(pndtRSGD) then begin
      EmitRSGDRows(
        e,
        sourceFile,
        planetFormID,
        planetEditorID,
        planetName,
        resourceCreationSeed,
        i,
        biomeRec,
        biomeChance,
        biomeUnknown0Raw,
        biomeUnknown0UInt32,
        'PNDT',
        pndtRSGD
      );
    end else if Assigned(biomRSGD) then begin
      EmitRSGDRows(
        e,
        sourceFile,
        planetFormID,
        planetEditorID,
        planetName,
        resourceCreationSeed,
        i,
        biomeRec,
        biomeChance,
        biomeUnknown0Raw,
        biomeUnknown0UInt32,
        'BIOM',
        biomRSGD
      );
    end else begin
      AddMessage(
        'No PNDT or BIOM RSGD for ' +
        planetEditorID + ', biome index ' + IntToStr(i)
      );
    end;
  end;
end;

function Finalize: Integer;
begin
  Result := 0;

  try
    sl.SaveToFile(OutPath);
    AddMessage('Export complete.');
    AddMessage('Rows written (excluding header): ' + IntToStr(sl.Count - 1));
    AddMessage('Saved to: ' + OutPath);
  finally
    sl.Free;
  end;
end;

end.
