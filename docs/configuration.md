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

The main features of the config are a list of steps of the pipeline, and a list of sources to pull data from.
Steps are executed in order, the first step producing a temporary flow output file, and subsequent steps generally operating on the output of the previous step and most of the time (but not always) producing a new (temporary) flow output files. Some steps may also produce different output artefacts than flows, such as a list of translatable strings, or logs or reports for QA. Subsequent steps cannot read such outputs, however. For more details about steps, see [steps].
There are different types of steps, and some types of steps may need additional input data that is used to create or operate on the input flows. Such data is defined in data sources, which may reference local files or files off the internet, in various formats. Steps then may reference one or multiple such data sources. For more details about steps, see [sources].

The *pull_data* operation takes data referenced by all sources and saves it in the local file system (folder `{inputpath}`) converted to json. It is agnostic of the actual steps.

The *compile_flows* operation executes the sequence of steps and writes the output to  `{flows_outputbasename}.json` in `{outputpath}`.

The config has the following fields:

- `meta`: meta information such as the pipeline version the config needs to be run with
- `inputpath`, `temppath` and `outputpath` (optional): Path to store/read input files, temp files, and output files.
- `flows_outputbasename`: Base filename of the output file and intermediate temp files.
- `output_split_number` (optional): Number of files to split the pipeline output (final flow definition) into.
    - Used to divide the file at the final step to get it to a manageable size that can be uploaded to RapidPro.
- `steps`: A list of steps. For more details, see [steps]
- `sources`: A dictionary of data sources. For more details, see [sources]
- `parents`: **Not Implemented** One (or multiple?) parent repos whose sources can be referenced

[sources]: sources.md
[steps]: steps.md
