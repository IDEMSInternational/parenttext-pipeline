# Configuration

A pipeline configuration allows us to specify what steps to run, with which parameters and with which input data.

## `config.json`

The pipeline is configured via a user-defined `config.json` file. This file is expected to be in the current working directory. If no such file is present, for backward-compatibility we also support configs via a `config.py` file.

## `config.py`

If no `config.json` was found, the pipeline will look for this file in the current working directory, load it, then attempt to call `create_config` to generate the configuration settings.

```python
def create_config():
    return {
        # Config settings here...
    }
```

The `create_config` callable must return a `dict` of configuration settings.

# Available settings

The main features of the config are a list of [steps] of the pipeline, and a list of [sources] to pull data from.
Steps are executed in order, the first step producing a temporary flow output file, and subsequent steps generally operating on the output of the previous step and most of the time (but not always) producing a new (temporary) flow output files. Some steps may also produce different output artefacts than flows, such as a list of translatable strings, or logs or reports for QA. Subsequent steps cannot read such outputs, however. For more details about steps, see [steps].
There are different types of steps, and some types of steps may need additional input data that is used to create or operate on the input flows. Such data is defined in data sources, which may reference local files or files off the internet, in various formats. Steps then may reference one or multiple such data sources. For more details about steps, see [sources].

The *pull_data* operation takes data referenced by all sources and saves it in the local file system (folder `{inputpath}`) converted to json. It is agnostic of the actual steps.

The *compile_flows* operation executes the sequence of steps and writes the output to `{flows_outputbasename}.json` in `{outputpath}`.

The config has the following fields:

- `sources`: A dictionary of data sources. For more details, see [sources]
- `steps`: A list of steps, often using data from the sources as input. For more details, see [steps]
- `sheet_names`: A dictionary of from sheet names to sheet_ids (**for Google sheets only**). 
   Sources can reference sheets by their ID or their sheet names.
- `parents`: One or multiple parent repos whose data can be referenced by the sources, see [hierarchy].
- `flows_outputbasename`: Base filename of the output file and intermediate temp files.
- `meta`: meta information such as the pipeline version the config needs to be run with
- `output_split_number` (optional): Number of files to split the pipeline output (final flow definition) into.
    - Used to divide the file at the final step to get it to a manageable size that can be uploaded to RapidPro.
- `inputpath`, `temppath` and `outputpath` (optional): Path to store/read input files, temp files, and output files.

An example of a configuration can be found in [hierarchy].

The python definition of the configuration model is available in [configs].

[sources]: sources.md
[steps]: steps.md
[hierarchy]: hierarchy.md
[configs]: ../src/parenttext_pipeline/configs.py