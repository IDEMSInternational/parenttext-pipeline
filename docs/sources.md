# Sources

Sources represent references to input data that may be used by [steps] of the pipeline, in various possible *source formats*. 

- `sheets`: Model-agnostic spreadsheet workbooks (a *spreadsheet* or *workbook* is a collection of individual *sheets*).
    - These may be in any of the following *subformats*:
        - `google_sheets`: Reference to a Google spreadsheet
        - `xlsx`: Reference to an XLSX file
        - `csv`: Reference to a folder of csv files representing the workbook.
        - `json`: Reference of a workbook in JSON format.
    - Each input file is converted into JSON workbook format; the resulting files a flatly stored in the output folder. In case of a name clash, a later file will overwrite an earlier file. (Processing order is `files_list` > `files_dict`)
- `json`: JSON files.
    - These are taken as is and copied to their new storage location.
    - Currently, only local file paths are supported.
- `translation_repo`: a format specifically for the translation step, see `TranslationSourceConfig` in [configs].
- `safeguarding`: a format specifically for the safeguarding step (to be deprecated), see `SafeguardingSourceConfig` in [configs].
- Remark: We may introduce a model-specific spreadsheet format with a master sheet indicating the model underlying each sheet in the future, so that the data can be validated and stored in a json format representing the (possibly nested) model.

Such data can be *pulled* to convert it into a github-friendly *storage format* (i.e. plaintext json) and store it locally. Once stored locally, such data can be used as input to individual steps of the *flow compilation* pipeline. The storage format is (so far) always json, and the exact structure of the json is domain specific, i.e. the user has to make sure that the data presented is in a format suitable for a specific pipeline step. In particular, it may be possible to represent input data in different *source formats* that yield the same data in the *storage format*.

## File referencing

The source config fully determines the storage location of the data in its *storage format*. All data is stored inside of `{config.inputpath}`. For each source, a subfolder `{source.id}` is created. 

### `json` and `sheets`

Within the source's subfolder, for each `(name, filepath)` entry in `{source.files_dict}`, the processed version of `{filepath}` is stored as `{name}.json`.

### `sheets` only

For the input format `sheets`, we can additionally use `files_list`.

- A special case here is if `files_archive` is provided and `source.subformat` is `csv`, then for each `sheet_id` entry in `source.files_list`, we process the folder `sheet_id` as a csv workbook and store the converted result as `{sheet_id}.json`. 
- Otherwise, for each `sheet_id` entry in `source.files_list`, the processed version of `sheet_id` is stored as `{sheet_id}.json`. Note that this currently only works if `source.subformat` is `google_sheets`, because we have not made a decision on how to turn full file paths into filenames. 
- Remark: Do we still need `files_archive` (`.zip` archive) support? I'd be keen to deprecate it.

[configs]: ../src/parenttext_pipeline/configs.py
[steps]: steps.md