# Requirements

- URL of a RapidPro host
- Account credentials (username, password) for a user with the 'Editor' role in a RapidPro workspace
- One or more flow definition (JSON) files to upload

# Run

## CLI

The command itself provides information on usage:

```
rpimport --help
```

For example:

```
rpimport --host https://example.com --user example --password pass flow_definition_1.json flow_definition_2.json
```

## Python import

From within your own Python script/application:

```
from parenttext_pipeline.importer import import_definition

import_definition(
    "https://example.com",
    "example",
    "pass",
    ["definition_file_1.json", "definition_file_2.json"],
)
```

# CI/CD

When running within continuous integration/deployment software, it is recommended that the password be kept secret at all times. The importer tool will not print any log messages containing the password.
