# Download media assets from Canto

## Command line interface

Ensure that:

- there is a [JSON configuration file](#JSON) in the current working directory
- the necessary [environment variables](#environment-variables) are set

```
python -m parenttext.canto destination_dir
```

Where `destination_dir` is the root directory under which all assets will be downloaded and stored.


## Configuration

### JSON

Create a configuration file called 'config.json' in the root directory of the deployment repository. If 'config.json' already exists, the following JSON should be merged into it.
```json
{
    "sources": {
        "media_assets": {
            "format": "media_assets",
            "mappings": {
                "Language": {
                    "Arabic": "ara"
                },
                "Caregiver Gender": {
                    "F": "female",
                    "M": "male"
                }
            },
            "path_template": [
                "media",
                "{% if format == 'audio' %}listen{% else %}look{% endif %}",
                "{{ (annotations['gender'] or 'unknown') }}",
                "{{ language or '' }}",
                "{{ name }}"
            ],
            "storage": {
                "system": "canto",
                "location": "your folder id",
                "annotations": {
                    "site_base_url": "https://example.canto.com"
                }
            }
        }
    }
}
```

The `mappings` property maps metadata values on assets from Canto to values that are required for a ParentText deployment. For example, any Canto asset with 'Arabic' as the value of the 'Language' property will have its value changed to 'ara'.

The `path_template` property determines the directory structure of the downloaded assets on the local filesystem. Each item in the list represents a directory; the last item represents the name of the media asset file. An item can be a static value or a [Jinja] template. Templates have access to the following information about each asset:

- `annotations`: transformed metadata properties from Canto
- `format`: for example, 'video', 'audio', 'image'
- `id`: Canto content id
- `language`: three-letter language code
- `name`: asset file name
- `folder`: asset's parent folder (or album in the case of Canto)

If any path element resolves to the empty string, that element will be ignored and the asset will be stored one level higher in the hierarchy. For example, if an asset would be stored under `audio/ara/name.m4a`, but the language metadata is not set, it would, instead, be stored under `audio/name.m4a`.

The `storage` property describes the system holding the assets and the location of assets within the system. The `location` property should be set to the ID of the folder containing all the assets to be downloaded. Canto-specific settings are stored under `annotations`:

- `site_base_url`: location of the Canto server

### Environment variables

Secret information needs to be passed to the Canto server in order to log in, these are passed into the app via environment variables:

- `CANTO_APP_ID`: ID generated when an API key is created in Canto
- `CANTO_APP_SECRET`: secret generated when an API key is created in Canto
- `CANTO_USER_ID`: user account that will be impersonated; should be the least privileged account able to download assets

When running the CLI tool, these environment variables can be automatically read from a file called '.env' in the current working directory. The file should contain a single key value pair on each line, for example:

```
CANTO_APP_ID=app_id
CANTO_APP_SECRET=secret
CANTO_USER_ID=user_id
```

### Compatibility with other media automation steps
The path template must download the files into the file structure used in the deployment asset server.

For the IDEMS Firebase this is (without loss of generality re the specific language codes):
```
📂 PATH/resourceGroup/
 ├── 📂 image
 │    └── 📂 universal
 ├── 📂 comic
 ├── 📂 voiceover
 │    └── 📂 resourceType
 │         ├── 📂 video
 │         │    └── 📂 gender
 │         │         ├── 📂 male
 │         │         │    └── 📂 language
 │         │         │         ├── 📂 eng
 │         │         │         └── 📂 spa
 │         │         └── 📂 female
 │         │              └── 📂 language
 │         │                   ├── 📂 eng
 │         │                   └── 📂 spa
 │         ├── 📂 audio
 │              └── 📂 gender
 │                   ├── 📂 male
 │                   │    └── 📂 language
 │                   │         ├── 📂 eng
 │                   │         └── 📂 spa
 │                   └── 📂 female
 │                        └── 📂 language
 │                             ├── 📂 eng
 │                             └── 📂 spa
 ```


[Jinja]: https://jinja.palletsprojects.com/en/stable/templates/
