# ParentText Pipeline

Handles the process for producing RapidPro flows from data held in spreadsheets.

# Setup

1. Install Python >= 3.10
2. Install Python dependencies: `pip install -e .`
3. Install Node and npm LTS versions
4. Install Node dependencies: `npm install`

# Run

To start the pipeline:

```
python -m parenttext_pipeline.cli
```

You will need to create a file called 'config.py', in the current working directory, and define a callable called 'create_config' that returns the pipeline settings as a dict. More details can be in the [configuration page][config].

# Documentation

- [Configuration][config] - details of configuration options for the pipeline
- [RapidPro flow importer] - to automatically import flow definitions into RapidPro
- [Archive tool] - to create snapshots of source Google Sheets to support repeatable pipeline runs
- [Transcode tool] - to prepare video and audio files that may be used by ParentText applications


[config]: docs/configuration.md
[Archive tool]: docs/archive.md
[RapidPro flow importer]: docs/rapidpro-import.md
[Transcode tool]: docs/transcode.md
