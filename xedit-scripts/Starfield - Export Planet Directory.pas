unit UserScript;

{
  Starfield - Export Planet Directory.pas

  Version: 4

  Purpose:
    Export a compact directory of PNDT records for joining against the
    runtime PlanetResourceExport data, including planetary Solar Power,
    Wind Power, and Planetary Habitation requirements.

  Tested target:
    xEdit / SF1Edit 4.1.5p

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
    PlanetNotLandable
    OceanWorld
    SolarArrayPower
    WindTurbinePower
    PlanetaryHabitationRank

  Derived gameplay columns:
    SolarArrayPower
      Basic Solar Array output selected by the PNDT temperature keyword:
        Deep Freeze             = 2
        Frozen / Cold           = 4
        Temperate / Hot         = 6
        Scorched / Inferno      = 8

    WindTurbinePower
      Basic Wind Turbine output selected by the PNDT atmosphere/pressure
      keywords:
        No atmosphere           = 0
        Thin                    = 3
        Standard                = 6
        High / Extreme          = 10

    PlanetaryHabitationRank
      Highest applicable requirement:
        Deep Freeze / Inferno   = rank 1
        Extreme pressure        = rank 2
        Corrosive / Toxic       = rank 3
        Extreme gravity         = rank 4
        Otherwise               = 0

  Notes:
    - "StarSystemID" is the numeric ID stored in PNDT\Body\GNAM - Galaxy Data.
      It is NOT a FormID.
    - "SystemName" is parsed from the display value, e.g.
          55539 (Katydid)
      -> StarSystemID = 55539
         SystemName   = Katydid
    - PlanetName is taken from Body\ANAM - Name, with FULL - Name as fallback.
    - Solar/Wind values are the authoritative integer output values of the
      basic Solar Array / Wind Turbine variants selected by the game data,
      not rounded percentages from an external website.
    - For non-landable bodies, SolarArrayPower, WindTurbinePower and
      PlanetaryHabitationRank are left blank.
    - Unexpected keyword combinations on landable planets/moons are logged as
      warnings so new/exceptional cases are not silently misclassified.
      BodyType = Orbital is excluded from these warnings because orbital PNDTs
      normally do not carry planetary temperature/pressure classifications.
    - Wind fallback: if a landable, non-Orbital body has a recognised atmosphere
      but no recognised pressure keyword, WindTurbinePower defaults to the basic
      turbine's standard/base output of 6 and a warning is logged.
    - The script is intended to be run on selected PNDT records or the PNDT group.

  Output:
    planet-directory.csv
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

function GetPlanetFullName(e: IInterface): string;
var
  i: Integer;
  comps, comp, compType, fullName: IInterface;
begin
  Result := '';

  { First preference: Body\ANAM - Name }
  Result := SafeGetEditValue(e, 'Body\ANAM - Name');
  if Result <> '' then
    Exit;

  { Fallback: find TESFullName_Component }
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

function HasPlanetNotLandableKeyword(e: IInterface): string;
var
  i, j: Integer;
  comps, comp, compType, kwda, kw: IInterface;
  kwValue: string;
begin
  Result := '0';

  comps := ElementByPath(e, 'Base Form Components');
  if not Assigned(comps) then
    Exit;

  { Find the BGSKeywordForm_Component rather than relying on a fixed component index. }
  for i := 0 to ElementCount(comps) - 1 do begin
    comp := ElementByIndex(comps, i);
    if not Assigned(comp) then
      Continue;

    compType := ElementByPath(comp, 'BFCB - Component Type');
    if not Assigned(compType) then
      Continue;

    if not SameText(GetEditValue(compType), 'BGSKeywordForm_Component') then
      Continue;

    kwda := ElementByPath(
      comp,
      'Component Data - Keywords\Keywords\KWDA - Keywords'
    );
    if not Assigned(kwda) then
      Exit;

    for j := 0 to ElementCount(kwda) - 1 do begin
      kw := ElementByIndex(kwda, j);
      if not Assigned(kw) then
        Continue;

      kwValue := UpperCase(GetEditValue(kw));

      { PlanetNotLandable [KYWD:000B04F3] }
      if Pos('[KYWD:000B04F3]', kwValue) > 0 then begin
        Result := '1';
        Exit;
      end;
    end;

    { A PNDT should only have one keyword component. }
    Exit;
  end;
end;


function HasPlanetKeyword(e: IInterface; const TargetEditorID: string): Boolean;
var
  i, j: Integer;
  comps, comp, compType, kwda, kw, linked: IInterface;
begin
  Result := False;

  if not Assigned(e) then
    Exit;

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

    if not SameText(GetEditValue(compType), 'BGSKeywordForm_Component') then
      Continue;

    kwda := ElementByPath(
      comp,
      'Component Data - Keywords\Keywords\KWDA - Keywords'
    );
    if not Assigned(kwda) then
      Exit;

    for j := 0 to ElementCount(kwda) - 1 do begin
      kw := ElementByIndex(kwda, j);
      if not Assigned(kw) then
        Continue;

      linked := nil;
      try
        linked := LinksTo(kw);
      except
        linked := nil;
      end;

      if not Assigned(linked) then
        Continue;

      if Signature(linked) <> 'KYWD' then
        Continue;

      if SameText(EditorID(linked), TargetEditorID) then begin
        Result := True;
        Exit;
      end;
    end;

    { A PNDT should only have one keyword component. }
    Exit;
  end;
end;


function HasAnyAtmosphereKeyword(e: IInterface): Boolean;
var
  i, j: Integer;
  comps, comp, compType, kwda, kw, linked: IInterface;
  edid: string;
begin
  Result := False;

  if not Assigned(e) then
    Exit;

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

    if not SameText(GetEditValue(compType), 'BGSKeywordForm_Component') then
      Continue;

    kwda := ElementByPath(
      comp,
      'Component Data - Keywords\Keywords\KWDA - Keywords'
    );
    if not Assigned(kwda) then
      Exit;

    for j := 0 to ElementCount(kwda) - 1 do begin
      kw := ElementByIndex(kwda, j);
      if not Assigned(kw) then
        Continue;

      linked := nil;
      try
        linked := LinksTo(kw);
      except
        linked := nil;
      end;

      if not Assigned(linked) then
        Continue;

      if Signature(linked) <> 'KYWD' then
        Continue;

      edid := EditorID(linked);
      if (Length(edid) >= Length('PlanetAtmosphereType')) and
         SameText(Copy(edid, 1, Length('PlanetAtmosphereType')),
                  'PlanetAtmosphereType') then begin
        if not SameText(edid, 'PlanetAtmosphereType00None') then begin
          Result := True;
          Exit;
        end;
      end;
    end;

    Exit;
  end;
end;

function GetSolarArrayPower(e: IInterface): string;
begin
  Result := '';

  if HasPlanetKeyword(e, 'PlanetTemperature00DeepFreeze') then
    Result := '2'
  else if HasPlanetKeyword(e, 'PlanetTemperature01Frozen') or
          HasPlanetKeyword(e, 'PlanetTemperature02Cold') then
    Result := '4'
  else if HasPlanetKeyword(e, 'PlanetTemperature03Temperate') or
          HasPlanetKeyword(e, 'PlanetTemperature04Hot') then
    Result := '6'
  else if HasPlanetKeyword(e, 'PlanetTemperature05Scorched') or
          HasPlanetKeyword(e, 'PlanetTemperature06Inferno') then
    Result := '8';
end;

function GetWindTurbinePower(e: IInterface; var UsedFallback: Boolean): string;
begin
  Result := '';
  UsedFallback := False;

  if HasPlanetKeyword(e, 'PlanetAtmosphereType00None') then
    Result := '0'
  else if HasPlanetKeyword(e, 'PlanetPressure01Thin') then
    Result := '3'
  else if HasPlanetKeyword(e, 'PlanetPressure02Terrestrial') then
    Result := '6'
  else if HasPlanetKeyword(e, 'PlanetPressure03High') or
          HasPlanetKeyword(e, 'PlanetPressure04Extreme') then
    Result := '10'
  else if HasAnyAtmosphereKeyword(e) then begin
    { Conservative anomaly fallback:
      an atmosphere is present but no known pressure keyword is available. }
    Result := '6';
    UsedFallback := True;
  end;
end;

function GetPlanetaryHabitationRank(e: IInterface): string;
var
  rank: Integer;
begin
  rank := 0;

  if HasPlanetKeyword(e, 'PlanetTemperature00DeepFreeze') or
     HasPlanetKeyword(e, 'PlanetTemperature06Inferno') then
    rank := 1;

  if HasPlanetKeyword(e, 'PlanetPressure04Extreme') then
    if rank < 2 then
      rank := 2;

  if HasPlanetKeyword(e, 'PlanetAtmosphereToxicity00Corrosive') or
     HasPlanetKeyword(e, 'PlanetAtmosphereToxicity01Toxic') then
    if rank < 3 then
      rank := 3;

  if HasPlanetKeyword(e, 'PlanetGravity03Extreme') then
    if rank < 4 then
      rank := 4;

  Result := IntToStr(rank);
end;

function RecordReferencesKeyword(e: IInterface; const TargetFormID: string): Boolean;
var
  i: Integer;
  child, linked: IInterface;
begin
  Result := False;

  if not Assigned(e) then
    Exit;

  { Recurse through containers. }
  if ElementCount(e) > 0 then begin
    for i := 0 to ElementCount(e) - 1 do begin
      child := ElementByIndex(e, i);
      if Assigned(child) then
        if RecordReferencesKeyword(child, TargetFormID) then begin
          Result := True;
          Exit;
        end;
    end;
    Exit;
  end;

  { For leaf/reference elements, resolve the linked record if there is one. }
  linked := nil;
  try
    linked := LinksTo(e);
  except
    linked := nil;
  end;

  if not Assigned(linked) then
    Exit;

  if Signature(linked) <> 'KYWD' then
    Exit;

  if SameText(IntToHex(FixedFormID(linked), 8), TargetFormID) then
    Result := True;
end;

function IsOceanWorld(e: IInterface): string;
var
  biomes, biomeEntry, biomeRef, biomeRecord: IInterface;
begin
  Result := '0';

  biomes := ElementByPath(e, 'Biomes');
  if not Assigned(biomes) then
    Exit;

  { OceanWorld requires exactly one biome entry. }
  if ElementCount(biomes) <> 1 then
    Exit;

  biomeEntry := ElementByIndex(biomes, 0);
  if not Assigned(biomeEntry) then
    Exit;

  biomeRef := ElementByPath(biomeEntry, 'Biome');
  if not Assigned(biomeRef) then
    Exit;

  biomeRecord := nil;
  try
    biomeRecord := LinksTo(biomeRef);
  except
    biomeRecord := nil;
  end;

  if not Assigned(biomeRecord) then
    Exit;

  if Signature(biomeRecord) <> 'BIOM' then
    Exit;

  { BiomeTypeOcean [KYWD:002C539E] }
  if RecordReferencesKeyword(biomeRecord, '002C539E') then
    Result := '1';
end;

function Initialize: Integer;
begin
  Result := 0;

  sl := TStringList.Create;

  { Capture one local timestamp for the entire extract. }
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
    'PlanetNotLandable' + ',' +
    'OceanWorld' + ',' +
    'SolarArrayPower' + ',' +
    'WindTurbinePower' + ',' +
    'PlanetaryHabitationRank'
  );

  OutPath := ScriptsPath + 'planet-directory.csv';
  AddMessage('Starfield Planet Directory export started.');
  AddMessage('Output: ' + OutPath);
end;

function Process(e: IInterface): Integer;
var
  sig, sourceFile, planetFormID, planetEditorID: string;
  planetName, bodyType: string;
  systemRaw, systemID, systemName: string;
  parentPlanetID, planetID: string;
  planetNotLandable, oceanWorld: string;
  solarArrayPower, windTurbinePower, planetaryHabitationRank: string;
  windUsedFallback: Boolean;
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

  planetName := GetPlanetFullName(e);
  bodyType := SafeGetEditValue(e, 'Body\CNAM - Body type');

  systemRaw := SafeGetEditValue(e, 'Body\GNAM - Galaxy Data\Star System ID');
  systemID := ExtractSystemID(systemRaw);
  systemName := ExtractParenText(systemRaw);

  parentPlanetID := SafeGetEditValue(e, 'Body\GNAM - Galaxy Data\Parent Planet ID');
  planetID := SafeGetEditValue(e, 'Body\GNAM - Galaxy Data\Planet ID');
  planetNotLandable := HasPlanetNotLandableKeyword(e);
  oceanWorld := IsOceanWorld(e);

  solarArrayPower := '';
  windTurbinePower := '';
  planetaryHabitationRank := '';

  { Ignore non-landable bodies for environmental outpost calculations. }
  if planetNotLandable = '0' then begin
    solarArrayPower := GetSolarArrayPower(e);
    windUsedFallback := False;
    windTurbinePower := GetWindTurbinePower(e, windUsedFallback);
    planetaryHabitationRank := GetPlanetaryHabitationRank(e);

    { Do not silently invent values for an unexpected landable world.
      Orbital PNDTs intentionally lack normal planetary environment keywords,
      so suppress Solar/Wind warnings for BodyType = Orbital. }
    if not SameText(bodyType, 'Orbital') then begin
      if solarArrayPower = '' then
        AddMessage(
          'WARNING: no recognized Solar temperature keyword for ' +
          planetEditorID + ' [' + planetFormID + ']'
        );

      if windUsedFallback then
        AddMessage(
          'WARNING: no recognized Wind pressure keyword for ' +
          planetEditorID + ' [' + planetFormID + ']; atmosphere present, ' +
          'using standard/base WindTurbinePower fallback = 6.'
        )
      else if windTurbinePower = '' then
        AddMessage(
          'WARNING: no recognized Wind atmosphere/pressure keyword for ' +
          planetEditorID + ' [' + planetFormID + ']'
        );
    end;
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
    CsvField(planetNotLandable) + ',' +
    CsvField(oceanWorld) + ',' +
    CsvField(solarArrayPower) + ',' +
    CsvField(windTurbinePower) + ',' +
    CsvField(planetaryHabitationRank)
  );
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
