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

Sources may have both. In this case, dict entries will overwrite list entries of the same name.

## Local storage locations

The source config fully determines the storage location of the data in its *storage format*. All data is stored inside of `{config.inputpath}`. When *pulling data*, each source gets its own local subfolder: For each source, a subfolder `{source.id}` is created. The list entries (str) and dict keys determine the filenames of the locally stored files.

Remark: The [configuration] has an (optional) global field `sheet_names` in which a mapping from names to sheet_ids can be provided. When a source references an input file, it first looks up whether it's in the `sheet_names` map and in that case uses the respective key as storage file path (while pulling the file in accordance to the `sheet_names` dict value). This is useful for Google sheets because their sheet_ids are non-descript, but potentially also for local file references to abbreviate them and avoid `/`.


### `json` and `sheets`

Within the source's subfolder, for each `(name, filepath)` entry in `{source.files_dict}`, the processed version of `{filepath}` is stored as `{name}.json`.

### `sheets` only

For the input format `sheets`, we can additionally use `files_list`.

- For each `sheet_name` entry in `source.files_list`, the processed version of `sheet_name` is stored as `{sheet_name}.json`. Note that the `sheet_name` may not contain certain special characters such as `/`.
- If the subformat is not `google_sheets`, i.e. we're referencing local files, the local file path is relative to the current working directory of the pipeline.
- It is possible to provide a `basepath` (relative or absolute) to the source config; then all file paths are relative to the `basepath`.
- It is also possible to provide a `files_archive` URL to a zip file. In that case, all file paths are relative to the archive root.

- Remark: Do we still need `files_archive` (`.zip` archive) support? I'd be keen to deprecate it.

Example: Assume that, relative to the current working directory, we have a folder `csv/safeguarding` containing `.csv` files, and we have a file `excel_files/safeguarding crisis.xlsx`. Then the following stores three copies of the `csv` data and three copies of the `xlsx` data, each in json format.

```
{
    "meta": {
        "version": "1.0.0",
        "pipeline_version": "1.0.0"
    },
    "parents": {},
    "flows_outputbasename": "parenttext_all",
    "output_split_number": 1,
    "sheet_names" : {
        "csv_safeguarding" : "csv/safeguarding",
        "xlsx_safeguarding" : "excel_files/safeguarding crisis.xlsx"
    },
    "sources": {
        "safeguarding_csv_dict": {
            "parent_sources": [],
            "format": "sheets",
            "subformat": "csv",
            "files_dict": {
                "safeguarding": "csv/safeguarding"
            }
        },
        "safeguarding_csv_list": {
            "parent_sources": [],
            "format": "sheets",
            "subformat": "csv",
            "files_list": [
                "csv_safeguarding"
            ]
        },
        "safeguarding_csv_list_remap": {
            "parent_sources": [],
            "format": "sheets",
            "subformat": "csv",
            "basepath": "csv",
            "files_list": [
                "safeguarding"
            ]
        },
        "safeguarding_xlsx_dict": {
            "parent_sources": [],
            "format": "sheets",
            "subformat": "xlsx",
            "files_dict": {
                "safeguarding": "excel_files/safeguarding crisis.xlsx"
            }
        },
        "safeguarding_xlsx_list_remap": {
            "parent_sources": [],
            "format": "sheets",
            "subformat": "xlsx",
            "files_list": [
                "xlsx_safeguarding"
            ]
        },
        "safeguarding_xlsx_list": {
            "parent_sources": [],
            "basepath": "excel_files",
            "format": "sheets",
            "subformat": "xlsx",
            "files_list": [
                "safeguarding crisis.xlsx"
            ]
        }
    },
    "steps": []
}
```

[configs]: ../src/parenttext_pipeline/configs.py
[configuration]: configuration.md
[steps]: steps.md
[hierarchy]: hierarchy.md
