# ParentText Pipeline

Public repository to handle the process for producing final RapidPro flows from data held in Google Sheets.

# Setup

1. Install Python >= 3.8
2. Install Python dependencies: `pip install -e .`
3. Install Node and npm LTS versions
4. Install Node dependencies: `npm install`

# Running pipeline

The file `pipelines.py` contains the general functions that can be used to run the pipeline.

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
