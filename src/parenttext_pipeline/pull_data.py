import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from rpft.converters import convert_to_json

from parenttext_pipeline.common import (
    clear_or_create_folder,
    get_input_subfolder,
    get_sheet_id,
    run_node,
    write_meta,
)
from parenttext_pipeline.extract_keywords import process_keywords_to_file


def run(config):
    clear_or_create_folder(config.inputpath)
    clear_or_create_folder(config.temppath)

    for name, source in config.sources.items():
        if source.format == "sheets":
            pull_sheets(config, source, name)
        elif source.format == "json":
            pull_json(config, source, name)
        elif source.format == "translation_repo":
            pull_translations(config, source, name)
        elif source.format == "safeguarding":
            pull_safeguarding(config, source, name)
        else:
            raise ValueError(f"Invalid source format {source.format}")

        print(f"Pulled all {name} data")

    meta = {
        "pull_timestamp": str(datetime.now(timezone.utc)),
    }
    write_meta(config, meta, config.inputpath)

    print("DONE.")


def pull_translations(config, source, source_name):
    for lang in source.languages:
        lang_code = lang["code"]
        translations_input_folder = Path(config.inputpath) / source_name / lang_code
        translations_temp_folder = Path(config.temppath) / source_name / lang_code

        if os.path.exists(translations_input_folder):
            shutil.rmtree(translations_input_folder)

        os.makedirs(translations_input_folder)
        os.makedirs(translations_temp_folder)

        # Download relevant PO translation files from github to temp folder
        language_folder_in_repo = source.folder_within_repo + "/" + lang_code
        translation_temp_po_folder = os.path.join(
            translations_temp_folder, "raw_po_files"
        )
        download_translations_github(
            source.translation_repo,
            language_folder_in_repo,
            translation_temp_po_folder,
        )

        # Convert PO to json and write these to input folder
        for root, dirs, files in os.walk(translation_temp_po_folder):
            for file in files:
                file_name = Path(file).stem
                source_file_path = os.path.join(root, file)
                dest_file_path = os.path.join(
                    translations_input_folder,
                    file_name + ".json",
                )
                run_node(
                    "idems_translation_common/index.js",
                    "convert",
                    source_file_path,
                    dest_file_path,
                )


def get_json_from_sheet_id(source, temp_dir, sheet_id):
    if source.subformat == "google_sheets":
        return convert_to_json(sheet_id, source.subformat)
    else:
        sheet_path = os.path.join(temp_dir, sheet_id)
        return convert_to_json(sheet_path, source.subformat)


def pull_sheets(config, source, source_name):
    # Download all sheets used for flow creation and edits and store as json
    source_input_path = get_input_subfolder(
        config, source_name, makedirs=True, in_temp=False
    )

    jsons = {}
    if source.files_archive is not None:
        if source.subformat == "google_sheets":
            raise ValueError(
                "files_archive not supported for sheets of subformat google_sheets."
            )
        location = source.archive
        archive_filepath = download_archive(config.temppath, location)
        temp_dir = tempfile.TemporaryDirectory()
        shutil.unpack_archive(archive_filepath, temp_dir)
    else:
        temp_dir = Path(source.basepath or ".")

    for sheet_name in source.files_list:
        sheet_id = get_sheet_id(config, sheet_name)
        jsons[sheet_name] = get_json_from_sheet_id(source, temp_dir, sheet_id)
    for new_name, sheet_name in source.files_dict.items():
        sheet_id = get_sheet_id(config, sheet_name)
        jsons[new_name] = get_json_from_sheet_id(source, temp_dir, sheet_id)

    if source.files_archive is not None:
        temp_dir.cleanup()

    for sheet_name, content in jsons.items():
        with open(
            source_input_path / f"{sheet_name}.json",
            "w",
            encoding="utf-8",
        ) as export:
            export.write(content)


def pull_json(config, source, source_name):
    # Postprocessing files
    source_input_path = get_input_subfolder(
        config, source_name, makedirs=True, in_temp=False
    )

    for new_name, filepath in source.files_dict.items():
        shutil.copyfile(filepath, source_input_path / f"{new_name}.json")


def pull_safeguarding(config, source, source_name):
    # Safeguarding files
    source_input_path = get_input_subfolder(
        config, source_name, makedirs=True, in_temp=False
    )
    safeguarding_file_path = source_input_path / "safeguarding_words.json"
    if source.sources:
        process_keywords_to_file(source.sources, safeguarding_file_path)
    else:
        shutil.copyfile(source.filepath, safeguarding_file_path)


def unpack_archive(destination, location):
    with tempfile.TemporaryDirectory() as temp_dir:
        location = download_archive(temp_dir, location)
        shutil.unpack_archive(location, destination)


def download_archive(destination, location):
    if location and location.startswith("http"):
        response = requests.get(location)

        if response.ok:
            archive_destinationpath = os.path.join(destination, "archive.zip")
            with open(archive_destinationpath, "wb") as archive:
                archive.write(response.content)
            print(f"Archive downloaded, url={location}, file={archive_destinationpath}")
        else:
            print(
                f"Archive download failed, "
                f"status={response.status_code}, url={location}"
            )

        return archive_destinationpath
    else:
        return location


def download_translations_github(repo_url, folder_path, local_folder):
    # Parse the repository URL to get the owner and repo name
    parts = repo_url.split("/")
    owner = parts[-2]
    repo_name = parts[-1].split(".")[0]  # Remove '.git' extension if present

    # Construct the GitHub API URL to get the contents of the folder
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{folder_path}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()

        if not os.path.exists(local_folder):
            os.makedirs(local_folder)

        for item in response.json():
            local_file_path = Path(local_folder) / item["name"]

            if item["type"] == "file" and local_file_path.suffix == ".po":
                response = requests.get(item["download_url"])
                response.raise_for_status()

                with open(local_file_path, "wb") as local_file:
                    local_file.write(response.content)

    except Exception as e:
        print("An error occurred:", e)
