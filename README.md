# ParentText Pipeline

Handles the process for producing RapidPro flows from data held in Google Sheets.

# Setup

1. Install Python >= 3.8
2. Install Python dependencies: `pip install -e .`
3. Install Node and npm LTS versions
4. Install Node dependencies: `npm install`

# Run

To start the pipeline:

```
python -m parenttext_pipeline.cli
```

You will need to create a file called 'config.py', in the current working directory, and define a callable called 'create_config' that returns the pipeline settings as a dict. More details can be in the [configuration page].

# RapidPro flow importer

A user account on a RapidPro server is required.

## CLI

```
rpimport --help
```

## Python import

```
from parenttext_pipeline.importer import import_definition

import_definition(
    host,
    username,
    password,
    definition_file,
)
```

# Archive tool

Used to create snapshots of source Google Sheets to support repeatable pipeline runs. See [archive tool docs] for details.


# Transcode

ParentText chatbots need supporting media files. This project contains a script that will transcode source video files to video and audio files that meet the ParentText specification.

## Requirements

The script uses the [FFmpeg] command, so it will need to be installed before the script can be used.

## CLI

```
python -m parenttext.transcode --help
```


[configuration page]: docs/configuration.md
[archive tool docs]: docs/archive.md
[FFmpeg]: https://ffmpeg.org/
