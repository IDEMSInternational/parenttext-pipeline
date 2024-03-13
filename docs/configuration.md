# Configuration

The pipeline is configured via a user-defined callable named `create_config` in a file called 'config.py'.

```python
def create_config():
    return {
        # Config settings here...
    }
```

On initialisation, the pipeline will look for this file in the current working directory, load it, then attempt to call `create_config` to generate the configuration settings.

The `create_config` callable must return a `dict` of configuration settings.

# Available settings

## sources

### sources.filename

The name prefix that will be used in filenames during processing.

### sources.spreadsheet\_ids

IDs of Google Sheets where the ParentText flows are defined.

### sources.crowdin\_name

Name of the file that is produced to send to translators.

### sources.tags

Used to identify flows to be process. Possible values for tag 1:

- onboarding
- dev\_assess
- ltp_activity
- home\_activity\_checkin
- module
- goal\_checkin
- safeguarding
- menu
- delivery

### sources.split\_no

The number of files into which the final flow definition will be split.

Used to divide the file at the final step to get it to a manageable size that can be uploaded to RapidPro.

## special\_expiration

Used to modify expiration times.

## default\_expiration

Used to modify expiration times.

## model

Name of the Python module containing data models to use as part of the process of converting data extracted from sheets.

## languages

A list of language definitions that will be looked for to localize back into the flows. Each language definition consists of:

- `language`: 3-letter language code used in RapidPro
- `code`: 2-letter code used in CrowdIn

## translation\_repo

Location of a git repository where translations are stored.

## folder\_within\_repo

The location within `tranlsation_repo` where translations are stored.

Used in conjuction with `translation_repo`, above.

## outputpath

Destination path for all files (including intermediary files and log files).

Default is 'output' within the current workin directory.

## qr\_treatment

How to process "quick replies". Valid values are:

- move: Remove quick replies and add equivalents to them to the message text, and give numerical prompts to allow basic phone users to use the app.
- reformat: Reformat quick replies so that long ones are added to the message text, as above.
- none: Do nothing.

## select\_phrases

The default phrase we want to add if quick replies are being moved to message text.

## add\_selectors

If `qr_treatment` is 'move', add some basic numerical quick replies back in. Valid values are 'yes' or 'no'.

## special\_words

Path to a file containing words we always want to keep as full quick replies.

## count\_threshold

When `qr_treatment` is 'reformat', set limits on the number of quick replies that are processed.

If the number of quick replies is below or equal to count\_threshold then the quick replies are left in place.

## length\_threshold

When `qr_treatment` is 'reformat', set limits on the number of quick replies that are processed.

If the character-length of the longest quick reply is below or equal to length\_threshold then the quick replies are left in place.

## ab\_testing\_sheet\_id

Google Sheets ID for Sheet containing AB testing data.

## localisation\_sheet\_id

Google Sheets ID.

## eng\_edits\_sheet\_id

Google Sheets ID for Sheet containing dict edits data.

## transl\_edits\_sheet\_id

Google Sheets ID.

## sg\_flow\_id

Sheets ID for Sheet containing safeguarding data.

## sg\_flow\_name

The name of the RapidPro flow for safeguarding.

## sg\_path

Path to file containing translated safeguarding words in JSON format.

## sg\_sources

Defines a list of sources containing safeguarding keywords. Each entry is a `dict` containing the following keys:

- `key`: three letter language code of the translated words
- `path`: file path on the local file system to the XLSX file containing the words

For example:
```python
{
    "sg_sources": [
        {
            "key": "spa",
            "path": "excel_files/safeguarding mexico.xlsx",
        },
    ],
}
```

The referenced XLSX files will be converted to a single file called _safeguarding\_words.json_, in the output directory. The `sg_path` setting will be overridden to point to this JSON file, for further processing. If `sg_sources` is not set, `sg_path` will remain unchanged.

## redirect\_flow\_names

Names of redirect flows to be modified as part of safeguarding process.
