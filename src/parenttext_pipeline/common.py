import itertools
import json
import os
import shutil
import subprocess
from pathlib import Path

from parenttext_pipeline import pipeline_version


def clear_or_create_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def get_input_subfolder(config, name, makedirs=False):
    source_input_path = Path(config.inputpath) / name
    if makedirs:
        os.makedirs(source_input_path)
    return source_input_path


def get_sheet_id(config, sheet_name):
    return config.sheet_names.get(sheet_name, sheet_name)


def input_files_from_ids(step_input_path, spreadsheet_ids):
    sheets = [
        os.path.join(step_input_path, f"{sheet_id}.json")
        for sheet_id in spreadsheet_ids
    ]
    return sheets


def get_source_config(config, source_name, step_name):
    source_config = config.sources.get(source_name)
    if source_config is None:
        raise ValueError(f"Step {step_name} references undefined source {source_name}")
    return source_config


def get_files_from_source(config, source_name, step_name):
    files_by_id = []
    source_config = get_source_config(config, source_name, step_name)
    if source_config.format not in ["sheets", "json"]:
        raise ValueError(
            f"Source {source_name} referenced by step {step_name} should be "
            "of format sheets or json but is not."
        )
    step_input_path = get_input_subfolder(config, source_name)
    # JSON input format currently doesn't support files_list
    for file_id in itertools.chain(
        getattr(source_config, "files_list", []), source_config.files_dict.keys()
    ):
        files_by_id.append((file_id, os.path.join(step_input_path, f"{file_id}.json")))
    return files_by_id


def get_files_list_from_source(config, source_name, step_name):
    files_by_id = get_files_from_source(config, source_name, step_name)
    return [pair[1] for pair in files_by_id]


def get_files_dict_from_source(config, source_name, step_name):
    files_by_id = get_files_from_source(config, source_name, step_name)
    return dict(files_by_id)


def get_full_step_files_list(config, step_config):
    files = []
    if not step_config.sources:
        raise ValueError(f"{step_config.id} step does not have any sources")
    for source in step_config.sources:
        files += get_files_list_from_source(config, source, step_config.id)
    return files


def get_full_step_files_dict(config, step_config):
    files = {}
    if not step_config.sources:
        raise ValueError(f"{step_config.id} step does not have any sources")
    for source in step_config.sources:
        files |= get_files_dict_from_source(config, source, step_config.id)
    return files


def make_output_filepath(config, suffix):
    return os.path.join(
        config.temppath,
        config.flows_outputbasename + suffix,
    )


def write_meta(config, field_dict, path):
    meta = {
        "pipeline_version": pipeline_version(),
        "config_version": config.meta.get("version") or "legacy",
    } | field_dict

    with open(Path(path) / "meta.json", "w") as outfile:
        json.dump(meta, outfile, indent=2)


def read_meta(path):
    with open(Path(path) / "meta.json") as infile:
        return json.load(infile)


def run_node(script, *args):
    subprocess.run(["node", "node_modules/@idems/" + script, *args])
