# Sources

Sources are an aggregation of data in the same format. Sources represent references to input data that may be used by [steps] of the pipeline.

Such data can be *pulled* to convert it into a github-friendly *storage format* (i.e. plaintext json) and store it locally. Once stored locally, such data can be used as input to individual steps of the *flow compilation* pipeline. The storage format is (so far) always json, and the exact structure of the json is domain specific, i.e. the user has to make sure that the data presented is in a format suitable for a specific pipeline step. In particular, it may be possible to represent input data in different *source formats* that yield the same data in the *storage format*.

Each source specifies a list and/or dict of files, a format (and possibly subformat) as well as an optional list of parent sources. For the use of parent sources, see [hierarchy].

## Formats

Source data can be in various possible *source formats*. 

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

## File referencing

Sources may have a list of data files as input (order matters). This can be specified as a list (order matters, as later sheets with the same name overwrite earlier sheets) or a dict.

Example list of files:

```
"edits_pretranslation": {
    "format": "sheets",
    "subformat": "google_sheets",
    "files_list": [
        "ab_testing_sheet_ID",
        "localisation_sheet_ID"
    ]
},
```

Example dictionary of files:

```
"qr_treatment": {
    "format": "json",
    "files_dict": {
        "select_phrases_file": "./edits/select_phrases.json",
        "special_words_file": "./edits/special_words.json"
    }
}
```

Sources may have both.

## Local storage locations

The source config fully determines the storage location of the data in its *storage format*. All data is stored inside of `{config.inputpath}`. When *pulling data*, each source gets its own local subfolder: For each source, a subfolder `{source.id}` is created. The list entries (str) and dict keys determine the filenames of the locally stored files.

Remark: For Google sheets, the sheet_ids are non-descript. Thus the [configuration] has an (optional) global field `sheet_names` in which a mapping from names to sheet_ids can be provided. When a source references an input file, it first looks up whether it's in the `sheet_names` map and in that case uses the respective values.


### `json` and `sheets`

Within the source's subfolder, for each `(name, filepath)` entry in `{source.files_dict}`, the processed version of `{filepath}` is stored as `{name}.json`.

### `sheets` only

For the input format `sheets`, we can additionally use `files_list`.

- A special case here is if `files_archive` is provided and `source.subformat` is `csv`, then for each `sheet_id` entry in `source.files_list`, we process the folder `sheet_id` as a csv workbook and store the converted result as `{sheet_id}.json`. 
- Otherwise, for each `sheet_id` entry in `source.files_list`, the processed version of `sheet_id` is stored as `{sheet_id}.json`. Note that this currently only works if `source.subformat` is `google_sheets`, because we have not made a decision on how to turn full file paths into filenames. 
- Remark: Do we still need `files_archive` (`.zip` archive) support? I'd be keen to deprecate it.

[configs]: ../src/parenttext_pipeline/configs.py
[configuration]: configuration.md
[steps]: steps.md
[hierarchy]: hierarchy.md
