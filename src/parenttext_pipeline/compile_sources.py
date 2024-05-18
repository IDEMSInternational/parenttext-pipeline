import os
from pathlib import Path
import shutil
import tempfile

from parenttext_pipeline.pull_data import unpack_archive
from parenttext_pipeline.configs import load_config


def compile_sources(repo_folder, destination_folder):
    """
    Compile flattened sources such that parent content is included directly.

    For each source, a folder is created within destination_folder with source data,
    and a source config is produced containing both the files from the parents
    and the child's own files.

    Args:
        repo_folder: local path to folder containing config
        destination_folder: local path where compiled input files should be written
    Returns:
        A list of sources based on the sources in config.json in the repo_folder,
        each source flattened so that parent content is included directly.
    """

    destination_folder = Path(destination_folder)
    repo_folder = Path(repo_folder)
    os.makedirs(destination_folder, exist_ok=True)
    config = load_config(repo_folder)
    parent_source_configs = {}
    for parent_id, parent in config.parents.items():
        parent_destination_folder = destination_folder / parent_id
        with tempfile.TemporaryDirectory() as temp_dir:
            unpack_archive(temp_dir, parent.location)
            # after extracting, all the stuff is inside a subfolder
            # which we need to identify.
            folder_contents = os.listdir(temp_dir)
            assert len(folder_contents) == 1
            archive_content_folder = Path(temp_dir) / folder_contents[0]
            parent_source_configs[parent_id] = compile_sources(
                archive_content_folder, parent_destination_folder
            )
    for source_id, source in config.sources.items():
        files_list = []
        files_dict = {}
        for parent_source in source.parent_sources:
            split = parent_source.split(".")
            assert len(split) == 2
            parent_id, psource_id = split
            psource = parent_source_configs[parent_id][psource_id]
            # Merge in parent file lists/dicts and copy referenced input files
            shutil.copytree(
                destination_folder / parent_id / psource_id,
                destination_folder / source_id,
                dirs_exist_ok=True,
            )
            for file in psource.files_list:
                files_list.append(file)
            for fileid, file in psource.files_dict.items():
                files_dict[fileid] = file
        source.files_list = files_list + source.files_list
        source.files_dict = files_dict | source.files_dict
        source.parents = []
    shutil.copytree(
        Path(repo_folder) / config.inputpath, destination_folder, dirs_exist_ok=True
    )
    return config.sources


# def compile_input(repo_folder, destination_folder):
# - read config in repo_folder, checkout each parent into a temp folder
# - recursive call on each parent
# 	--> compiles each parent into a destination folder (within the temp?)
# 	--> each (parent) source -- when compiled -- corresponds to a folder of data
# - for each source:
# 	- copy compiled parent content into the destination child folder for each parent
# 	- copy the child content on top (from input/)
