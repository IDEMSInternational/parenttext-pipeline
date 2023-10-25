# Overview

The archive tool creates snapshots of the input spreadsheets and packages them up in a zip archive. It was intended to support repeatable runs of the pipeline, by essentially freezing the state of all input spreadsheets at a point in time. It attempts to avoid the potential problem of Google Sheets being updated incorrectly and causing a pipeline run to fail.

# Create an archive

```
python -m parenttext_pipeline.archive
```

# Configuration

The archive tool will create a zip archive for each item in the `sources` and will name each archive with the `filename` of the source.

For example, for the following configuration:

```python
{
    "sources": [
        {
            "filename": "my_source",
            "spreadsheet_ids": ["id_1", "id_2"],
        },
    ],
    "outputpath": "my_output",
}
```

An archive called `my_output/my_source.zip` will be create in the current directory, containing the two spreadsheets defined.

# Run the pipeline from an archive

Each source must define the location of the archive to use.

```python
{
    "sources": [
        {
            "filename": "my_source",
            "spreadsheet_ids": ["id_1", "id_2"],
            "archive": "my_source.zip"
        }
    ]
}
```

Then run the pipeline as usual.

`archive` can be a reference to a file on the local filesystem or a URL (be careful!).

# Converting Google Sheets to CSV

The main purpose of the archive tool is to convert Google Sheets to CSV so that they may be saved for later use. Google Sheets may contain multiple "sheets" within them, but an individual CSV file can only represent a single sheet. Therefore, Google Sheets with multiple sheets must be arranged in separate CSV files in a hierarchy on the filesystem.

A single sheet will be arranged as follows:

```
google_sheet_id
├── sheet_1.csv
└── sheet_2.csv
```

An archive containing multiple source Google Sheets will be arranged as follows:

```
my_archive.zip
├── google_sheet_id_1
│   ├── sheet_1.csv
│   └── sheet_2.csv
└── google_sheet_id_2
    ├── sheet_1.csv
    └── sheet_2.csv
```

# Known issues

## Illegal characters in file paths

File names in the archive will be cut at the point an illegal character is encountered.

Windows:

```
< (less than)
> (greater than)
: (colon - sometimes works, but is actually NTFS Alternate Data Streams)
" (double quote)
/ (forward slash)
\ (backslash)
| (vertical bar or pipe)
? (question mark)
* (asterisk)
```

Linux:

```
/ (forward slash)
```

MacOS:

```
: (colon)
/ (forward slash)
```
