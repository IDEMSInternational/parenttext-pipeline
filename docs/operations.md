# Overview

The pipeline tool supports different operations. To run the pipeline performing a sequence of operations:

```
python -m parenttext_pipeline.cli operation1 operation2 ...
```

In order to run a pipeline, you must have a configuration file, see [configuration page][config] for more details.

Two operations are currently available:

## `pull_data`

Read data from various sources (which are defined in the config) and store them locally in json format.
The data will be written to the input folder specified in the config.
Different input formats are supported, and the data for each source is written to its own subfolder, see [sources].

The purpose of this is to a ensure that `compile_flows` runs of the pipeline are reproducable, by essentially freezing the state of all input spreadsheets at a point in time. It attempts to avoid the potential problem of Google Sheets being updated incorrectly and causing a pipeline run to fail. The `compile_flows` pipeline will only read locally stored data that has been pulled beforehand.


## `compile_flows`

Compile RapidPro flows from locally stored json files that have been pulled using `pull_data`.
Compiling flows involves multiple processing steps that are defined in the config, see [steps].


[config]: configuration.md
[steps]: steps.md
[sources]: sources.md

# Non-pipeline tools

## `parenttext.media_ops`
Runs the automated media operations, downloads from canto, transcodes files, and uploads to Firebase.
Has a dry run option `-d` to dry run without performing upload.
Typically pulls all needed inputs from `config.json`, but inputs can be manually set as described by the `--help`.