# Download media assets from Canto

## Command line interface

```
python -m parenttext.canto destination_dir
```

Where `destination_dir` is the root directory under which all assets will be downloaded and stored.


## Configuration

Create a configuration file called 'config.json' in the root directory of the deployment repository. If 'config.json' already exists, the following JSON should be merged into it.
```json
{
    "sources": {
        "media_assets": {
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
                "{{ format | title }}",
                "{{ (annotations['Caregiver Gender'] or '') | title }}",
                "{{ (language or '') | title }}",
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

The `path_template` property determines the directory structure of the downloaded assets on the local filesystem. Each item in the list represents a directory; the last item represents the name of the media asset file. An item can be a static value or a Jinja template. Templates have access to the following information about each asset:

- `annotations`: transformed metadata properties from Canto
- `format`: for example, 'video', 'audio', 'image'
- `id`: Canto content id
- `language`: three-letter language code
- `name`: asset file name

If any path element resolves to the empty string, that element will be ignored and the asset will be stored one level higher in the hierarchy. For example, if an asset would be stored under `audio/ara/name.m4a`, but the language metadata is not set, it would, instead, be stored under `audio/name.m4a`.

The `storage` property describes the system holding the assets and the location of assets within the system. The `location` property should be set to the ID of the folder containing all the assets to be downloaded. Canto-specific settings are stored under `annotations`:

- `site_base_url`: location of the Canto server

Secret information needs to be passed to the Canto server in order to log in, these are passed into the app via environment variables:

- `CANTO_APP_ID`: ID generated when an API key is created in Canto
- `CANTO_APP_SECRET`: secret generated when an API key is created in Canto
- `CANTO_USER_ID`: user account that will be impersonated; should be the least privileged account able to download assets
