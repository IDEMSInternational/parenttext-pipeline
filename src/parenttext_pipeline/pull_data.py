import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import concurrent.futures

import requests
from googleapiclient.discovery import build
from rpft.converters import convert_to_json
from rpft.google import Drive

from parenttext_pipeline.common import (
    clear_or_create_folder,
    get_input_folder,
    get_input_subfolder,
    get_sheet_id,
    run_node,
    write_meta,
    read_meta,
)
from parenttext_pipeline.extract_keywords import process_keywords_to_file


def run(config):
    # Get last update timestamp
    try:
        meta = read_meta(get_input_folder(config, in_temp=False))
        last_update_str = meta["pull_timestamp"]
        last_update = datetime.fromisoformat(last_update_str)
    except (FileNotFoundError, KeyError):
        print("meta.json not found, updating everything")
        last_update = None

    # Only clear the temp path; the input path is now managed incrementally
    clear_or_create_folder(config.temppath)

    for name, source in config.sources.items():
        if source.format == "sheets":
            pull_sheets(config, source, name, last_update)
        elif source.format == "json":
            pull_json(config, source, name)
        elif source.format == "translation_repo":
            pull_translations(config, source, name, last_update)
        elif source.format == "safeguarding":
            pull_safeguarding(config, source, name)
        elif source.format == "media_assets":
            continue
        else:
            raise ValueError(f"Invalid source format {source.format}")

        print(f"Pulled all {name} data")

    meta = {
        "pull_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    write_meta(config, meta, config.inputpath)

    print("DONE.")


def pull_translations(config, source, source_name, last_update):
    for lang in source.languages:
        lang_code = lang["code"]
        translations_input_folder = Path(config.inputpath) / source_name / lang_code
        translations_temp_folder = Path(config.temppath) / source_name / lang_code

        # The temp folder for raw .po files is cleared and recreated each time
        translation_temp_po_folder = Path(translations_temp_folder) / "raw_po_files"
        clear_or_create_folder(translation_temp_po_folder)
        os.makedirs(translations_input_folder, exist_ok=True)

        # Download relevant PO translation files from github to temp folder
        language_folder_in_repo = source.folder_within_repo + "/" + lang_code
        download_translations_github(
            source.translation_repo,
            language_folder_in_repo,
            str(translation_temp_po_folder),
            last_update,
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


def pull_sheets(config, source, source_name, last_update):
    source_input_path = get_input_subfolder(
        config, source_name, makedirs=True, in_temp=False
    )
    temp_dir_obj = None
    if getattr(source, "files_archive", None) is not None:
        if source.subformat == "google_sheets":
            raise ValueError(
                "files_archive not supported for sheets of subformat google_sheets."
            )
        archive_filepath = download_archive(config.temppath, source.archive)
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = Path(temp_dir_obj.name)
        shutil.unpack_archive(archive_filepath, temp_dir)
    else:
        temp_dir = Path(getattr(source, "basepath", None) or ".")

    files_list = getattr(source, "files_list", [])
    files_dict = getattr(source, "files_dict", {})
    all_sheets = {
        sheet_name: get_sheet_id(config, sheet_name) for sheet_name in files_list
    }
    all_sheets.update(
        {
            new_name: get_sheet_id(config, sheet_name)
            for new_name, sheet_name in files_dict.items()
        }
    )

    # Check that the drive credentials work before N auth tabs are opened
    Drive.client()

    sheets_to_download = {}

    modified_time_dict = Drive.get_modified_time(all_sheets.values())

    for sheet_name, sheet_id in all_sheets.items():
        modified_time = modified_time_dict[sheet_id]
        if (
            not last_update
            or (modified_time and modified_time > last_update)
            or not Path(source_input_path / f"{sheet_name}.json").exists()
        ):
            sheets_to_download[sheet_name] = all_sheets[sheet_name]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_sheet = {
            executor.submit(
                get_json_from_sheet_id, source, temp_dir, sheet_id
            ): sheet_name
            for sheet_name, sheet_id in sheets_to_download.items()
        }
        for future in concurrent.futures.as_completed(future_to_sheet):
            sheet_name = future_to_sheet[future]
            try:
                content = future.result()
                with open(
                    source_input_path / f"{sheet_name}.json", "w", encoding="utf-8"
                ) as f:
                    f.write(content)
                print(f"Pulled updated sheet: {sheet_name}")
            except Exception as e:
                print(f"Error downloading sheet '{sheet_name}': {e}")

    # Clean up local files that are no longer in the source config
    expected_files = {f"{name}.json" for name in all_sheets.keys()}
    for local_file in source_input_path.glob("*.json"):
        if local_file.name not in expected_files:
            print(f"Removing obsolete sheet file: {local_file.name}")
            local_file.unlink()

    if temp_dir_obj:
        temp_dir_obj.cleanup()


def pull_json(config, source, source_name):
    # Postprocessing files
    source_input_path = get_input_subfolder(
        config, source_name, makedirs=True, in_temp=False
    )

    for new_name, filepath in source.files_dict.items():
        shutil.copyfile(filepath, source_input_path / f"{new_name}.json")


def is_google_drive_file_id(location):
    return bool(re.fullmatch(r"[a-z0-9_-]{33}", location, re.IGNORECASE))


def is_google_sheets_id(location):
    return bool(re.fullmatch(r"[a-z0-9_-]{44}", location, re.IGNORECASE))


def pull_safeguarding(config, source, source_name):
    keywords_file_path = (
        get_input_subfolder(config, source_name, makedirs=True, in_temp=False)
        / "safeguarding_words.json"
    )

    if source.sources:

        dest = get_input_subfolder(config, source_name, makedirs=True, in_temp=True)

        for s in source.sources:
            location = s.get("location") or s["path"]
            content = None

            if is_google_drive_file_id(location):
                name, content = Drive.fetch(location)
                s["location"] = Path(dest) / (location + Path(name).suffix)
            elif is_google_sheets_id(location):
                ext = ".xlsx"
                name, content = Drive.export(location, ext=ext)
                s["location"] = (Path(dest) / location).with_suffix(ext)

            if content:
                with open(s["location"], "wb") as f:
                    f.write(content)

        process_keywords_to_file(source.sources, keywords_file_path)
    else:
        shutil.copyfile(source.filepath, keywords_file_path)


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


def get_github_last_commit_date(repo_url, file_path_in_repo):

    try:
        parts = repo_url.split("/")
        owner = parts[-2]
        repo_name = parts[-1].replace(".git", "")
        commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?path={file_path_in_repo}&page=1&per_page=1"
        response = requests.get(commits_url)
        response.raise_for_status()
        commit_data = response.json()
        if commit_data:
            commit_date_str = commit_data[0]["commit"]["committer"]["date"]
            if commit_date_str.endswith("Z"):
                commit_date_str = commit_date_str[:-1] + "+00:00"
            return datetime.fromisoformat(commit_date_str)
    except Exception as e:
        print(f"Could not get commit date for {file_path_in_repo}: {e}")
    return None


def download_translations_github(repo_url, folder_path, local_folder, last_update):
    parts = repo_url.split("/")
    owner = parts[-2]
    repo_name = parts[-1].split(".")[0]

    try:
        api_url = (
            f"https://api.github.com/repos/{owner}/{repo_name}/contents/{folder_path}"
        )
        response = requests.get(api_url)
        response.raise_for_status()
        remote_files = {
            item["name"]: item for item in response.json() if item["type"] == "file"
        }
    except Exception as e:
        print(f"An error occurred fetching file list from GitHub: {e}")
        return

    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?page=1&per_page=1"
        response = requests.get(api_url)
        response.raise_for_status()
        most_recent_commit = response.json()[0]["sha"]
    except Exception as e:
        print(f"An error occurred fetching most recent commit from GitHub: {e}")
        return
    
    if last_update is not None:

        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?page=1&per_page=1&until={last_update}"
            response = requests.get(api_url)
            response.raise_for_status()
            last_update_commit = response.json()[0]["sha"]
        except Exception as e:
            print(f"An error occurred fetching file list from GitHub: {e}")
            return

        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo_name}/compare/{last_update_commit}...{most_recent_commit}"
            response = requests.get(api_url)
            response.raise_for_status()
            changed_file_list = [
                item["filename"]
                for item in response.json()["files"]
                if folder_path in item["filename"]
            ]
        except Exception as e:
            print(f"An error occurred fetching changed file list from GitHub: {e}")
            return
        
        files_to_download = {
            key: value
            for key, value in remote_files.items()
            if value["path"] in changed_file_list and value["path"].endswith(".po")
        }
    else:
        files_to_download = {
            key: value
            for key, value in remote_files.items()
            if folder_path in value["path"] and value["path"].endswith(".po")
        }

    def download_worker(item):
        try:
            res = requests.get(item["download_url"])
            res.raise_for_status()
            with open(Path(local_folder) / item["name"], "wb") as f:
                f.write(res.content)
            print(f"Pulled updated translation: {item['name']}")
        except Exception as e:
            print(f"Error downloading translation '{item['name']}': {e}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_worker, files_to_download.values())

    # Clean up local files that no longer exist on the remote
    local_files = {p.name for p in Path(local_folder).glob("*.po")}
    obsolete_files = local_files - remote_files.keys()
    for file_name in obsolete_files:
        print(f"Removing obsolete translation file: {file_name}")
        (Path(local_folder) / file_name).unlink()
