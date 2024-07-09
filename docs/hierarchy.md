# Hierarchy

Many of our chatbots share common data. Rather than duplicating that for each, we want to split this shared data out to parent repositories.

A repository can specify one or multiple parent repos. Sources of the child repo can reference sources of parent repos, allowing to compose the list/dict of files within a source from the list/dict of parent sources in addition to the locally specified files.

Parents are specified as part of the main [configuration], for example:

```
"parents": {
    "parent1": {
        "location": "https://github.com/<org>/<repo>/archive/refs/heads/main.zip"
    },
    "parent2": {
        "location": "https://github.com/<org>/<repo>/archive/refs/tags/1.0.0.zip"
    }

}
```

Parents are repositories that currently have to be referenced to as zip files.
The location format may be expanded in the future, see #134 and #130.

## Source composition

In addition to a list/dict of file references, a source may reference other parent sources to compose its list/dict of files from:

```
"my_source": {
	"parent_sources": [
		"parent1.some_source",
		"parent1.other_source"
		"parent2.some_source"
	],
	"files_dict": {...},
	"files_list": [...]
}
```

When *pulling data*, only data from the files list/dict is locally stored (in the folder for this source), compare with [sources].

When running the flow compilation pipeline, source lists are taken from the parent repos (recursively) and file lists/dicts are composed as follows:

- The file lists of all parent_sources are concatenated (in order), with the own files_list concatenated at the end.
- The file dicts of all parent_sources and the own files_dict are merged. (In case of duplicate keys, the latter value is taken.) (**Note:** This may not be what we want: The use case for dicts is for steps that have specific input files, where each key has a semantic meaning. In case of a collision in dict keys, the child data overwrites the parent entry, which means there is no clean way of a step reading multiple input files of the same type (key) and merging them. We might prefer to have each dict value be a list of files, so that in a case of key collision, we can concatenate them.)

Thus when a pipeline step references a source, it has access to a joint files list/dict.


# An Example

Let's try to build an example showcasing inheritance:

Assume we have a grandparent repo living at the URL `grandparent_url`. Let its config be:

```
{
    "parents": {},
    "sheet_names" : {
        "grandparent_templates" : "google_sheet_id",
        ...
    },
    "sources": {
        "flow_definitions": {
            "format": "sheets",
            "subformat": "google_sheets",
            "files_list": [
                "grandparent_templates",
                "some_other_google_sheet_id_which_we_didnt_give_a_name",
                ...
            ]
        }
    },
    "steps": [
        # maybe this repo defines a pipeline to produce flows,
        # but maybe it only defines data sources and this list is empty
        ...
    ]
}
```

Assume we have a parent repo living at the URL `parent_url`. It declares the grandparent repo to be its parent (optionally specifying a branch/tag/commit hash), and references some of its sources. It defines two data sources, one for flows which references the parent repo, and one for flow expiration times. For the flows data source, the resulting input data (for the pipeline) is the grandparent list of sheets concatenated with the own list of sheets. However, when pulling data, only the own data is locally stored (for archiving on github).

Let it also define a pipeline that produces flows. Then the config could look like this:

```
{
    "parents": {
        "grandparent1": {
            "location": "grandparent_url"
        }
    },
    "sheet_names" : {
        "base_templates" : "google_sheet_idA",
        "base_content" : "google_sheet_idB",
        ...
    },
    "sources": {
        "flow_definitions": {
            "parent_sources": ["grandparent1.flow_definitions"],
            "format": "sheets",
            "subformat": "google_sheets",
            "files_list": [
                "base_templates",
                "base_content",
                ...
            ]
        },
        "expiration_times": {
            "format": "json",
            "files_dict": {
                "special_expiration_file": "./edits/specific_expiration.json"
            }
        }
    },
    "steps": [
        {   
            "id": "create_flows",
            "type": "create_flows",
            "sources": ["flow_definitions"],
            "models_module": "models.parenttext_models",
            "tags": [4,"response"]
        },
        {
            "id": "update_expiration_times",
            "type": "update_expiration_times",
            "sources": ["expiration_times"],
            "default_expiration_time": 1440
        }
    ]
}
```

Finally, let's define the child repo. Its two data sources inherit from the parent, and its flow data source recursively inherits from the grandparent. Again, these lists of input files are concatenated and used in the pipeline step referencing these sources, but when pulling data, only the child data is stored locally. For the second data source, we have a dict rather than a list of files, which is merged with the parent dict. (**Note:** This may not be what we want, because in case of a collision in dict keys, the child data overwrites the parent entry. We might prefer to have each dict value be a list of files, so that in a case of key collision, we can concatenate them? The use case for dicts is for steps that have specific input files, where each key has a semantic meaning. Using `special_expiration_file` and `special_expiration_file_child` and having the step infer from a name pattern that these are the same kind of data is ugly.)

```
{
    "parents": {
        "parent1": {
            "location": "parent_url"
        }
    },
    "sheet_names" : {
        "localised_sheets" : "google_sheet_id1",
        "N_onboarding_data" : "google_sheet_id2",
        "T_onboarding" : "google_sheet_id3",
        ...
    },
    "sources": {
        "flow_definitions": {
            "parent_sources": ["parent1.flow_definitions"],
            "format": "sheets",
            "subformat": "google_sheets",
            "files_list": [
                "N_onboarding_data",
                "T_onboarding",
                ...
                "localised_sheets"
            ]
        },
        "expiration_times": {
            "parent_sources": ["parent1.expiration_times"],
            "format": "json",
            "files_dict": {
                "special_expiration_file_child": "./edits/specific_expiration.json"
            }
        }
    },
    "steps": [
        {   
            "id": "create_flows",
            "type": "create_flows",
            "sources": ["flow_definitions"],
            ...
        },
        {
            "id": "update_expiration_times",
            "type": "update_expiration_times",
            "sources": ["expiration_times"],
            ...
        }
    ]
}
```

# Workflows and recommendations

A repository only stores its own data, not the data that it references from parent repos. Thus, in order to make pipeline runs fully reproducable, a repo should reference a specific snapshot of a parent repo, such as a tag or commit hash.

So instead of referencing
```
"location": "https://github.com/<org>/<repo>/archive/refs/heads/main.zip"
```

it is better to use
```
"location": "https://github.com/<org>/<repo>/archive/refs/tags/1.0.0.zip"
```

or
```
"location": "https://github.com/<org>/<repo>/archive/<commit-hash>.zip"
```

## Development

However, it may be cumbersome to use commits/tags when changing content in e.g. the grandparent repo, when you want to test the effects of the changes downstream in the child repo.
In this case, it is worthwhile having a `dev` branch for grandparent, parent and child, with the parent referencing the `dev` branch of the grandparent, and the child referencing the `dev` branch of the parent.
Then in the scenario above can be realized as follows:

- Modify sheets referenced by the grandparent
- run `pull_data` for the grandparent, and commit the `input` folder to its `dev` branch
- run `compile_flows` in the child repo (and inspect the output)

In the future, it may be possible to reference local paths to repositories, which may simplify this process by avoiding the need to make commits to higher-level repos for each change, see #134.

## Releases

If you have made changes to various levels of the hierarchy in their respective `dev` branches, and want to make a new deployment release for the child repo, you will need to do the following changes:

- grandparent:
	- Merge `dev` into `main`
	- create a new release e.g. `1.1.0`
- parent:
	- make a commit on top of `dev` updating the location of the grandparent in the config to reflect the new tag `1.1.0`
	- merge this into `main`
	- create a new release, e.g. `0.2.1`
- child:
	- make a commit on top of `dev` updating the location of the parent in the config to reflect the new tag `0.2.1`
	- merge this into `main`
	- create a new release

[configuration]: configuration.md
[sources]: sources.md
