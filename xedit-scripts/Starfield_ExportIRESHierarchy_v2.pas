unit Starfield_ExportIRESHierarchy;

{
  Exports selected Starfield IRES records to CSV.

  Columns:
    FormID
    EditorID
    Name
    Rarity
    ChildFormID
    ChildEditorID
    ChildName
    ChildRarity

  Behaviour:
  - Supports one or more selected IRES records.
  - Emits one row per parent -> child relationship.
  - If a parent has multiple child resources, the parent fields are repeated.
  - If a parent has no child resources, one row is emitted with blank child fields.
  - Output is read-only and written to the xEdit Edit Scripts folder.
}

var
  sl: TStringList;
  outputPath: string;

function CsvEscape(const s: string): string;
var
  t: string;
begin
  t := StringReplace(s, '"', '""', [rfReplaceAll]);
  Result := '"' + t + '"';
end;

function HexFormID(e: IInterface): string;
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

function SafeName(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  try
    Result := GetElementEditValues(e, 'FULL - Name');
  except
    Result := '';
  end;

  if Result = '' then
    try
      Result := GetElementEditValues(e, 'FULL');
    except
      Result := '';
    end;
end;

function SafeRarity(e: IInterface): string;
begin
  Result := '';
  if not Assigned(e) then
    Exit;

  try
    Result := GetElementEditValues(e, 'SNAM - Rarity');
  except
    Result := '';
  end;
end;

procedure AddRow(parentRec, childRec: IInterface);
var
  formIDValue, editorIDValue, nameValue, rarityValue: string;
  childFormIDValue, childEditorIDValue, childNameValue, childRarityValue: string;
begin
  formIDValue := HexFormID(parentRec);
  editorIDValue := SafeEditorID(parentRec);
  nameValue := SafeName(parentRec);
  rarityValue := SafeRarity(parentRec);

  childFormIDValue := '';
  childEditorIDValue := '';
  childNameValue := '';
  childRarityValue := '';

  if Assigned(childRec) then begin
    childFormIDValue := HexFormID(childRec);
    childEditorIDValue := SafeEditorID(childRec);
    childNameValue := SafeName(childRec);
    childRarityValue := SafeRarity(childRec);
  end;

  sl.Add(
    CsvEscape(formIDValue) + ',' +
    CsvEscape(editorIDValue) + ',' +
    CsvEscape(nameValue) + ',' +
    CsvEscape(rarityValue) + ',' +
    CsvEscape(childFormIDValue) + ',' +
    CsvEscape(childEditorIDValue) + ',' +
    CsvEscape(childNameValue) + ',' +
    CsvEscape(childRarityValue)
  );
end;

function Initialize: Integer;
begin
  Result := 0;

  sl := TStringList.Create;
  sl.Add(
    'FormID,' +
    'EditorID,' +
    'Name,' +
    'Rarity,' +
    'ChildFormID,' +
    'ChildEditorID,' +
    'ChildName,' +
    'ChildRarity'
  );

  outputPath := ScriptsPath + 'Starfield_IRES_Hierarchy.csv';

  AddMessage('Starfield IRES hierarchy export started.');
end;

function Process(e: IInterface): Integer;
var
  children, childElement, childRec: IInterface;
  i, childCount: Integer;
begin
  Result := 0;

  if not Assigned(e) then
    Exit;

  if ElementType(e) <> etMainRecord then
    Exit;

  if Signature(e) <> 'IRES' then begin
    AddMessage('Skipping non-IRES record: ' + Name(e));
    Exit;
  end;

  children := ElementByPath(e, 'Child Resources');

  if not Assigned(children) then begin
    AddRow(e, nil);
    Exit;
  end;

  childCount := ElementCount(children);

  if childCount = 0 then begin
    AddRow(e, nil);
    Exit;
  end;

  for i := 0 to childCount - 1 do begin
    childElement := ElementByIndex(children, i);
    childRec := nil;

    if Assigned(childElement) then
      try
        childRec := LinksTo(childElement);
      except
        childRec := nil;
      end;

    if Assigned(childRec) and (Signature(childRec) = 'IRES') then
      AddRow(e, childRec)
    else
      AddRow(e, nil);
  end;
end;

function Finalize: Integer;
begin
  Result := 0;

  try
    sl.SaveToFile(outputPath);
    AddMessage('Saved: ' + outputPath);
    AddMessage('Rows exported: ' + IntToStr(sl.Count - 1));
  finally
    sl.Free;
  end;
end;

end.
