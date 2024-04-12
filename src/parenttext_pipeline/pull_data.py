import os
import requests
import shutil
import tempfile
from pathlib import Path
from parenttext_pipeline.common import clear_or_create_folder, Config, get_step_config, run_node
from rpft.converters import convert_to_json

from parenttext_pipeline.extract_keywords import process_keywords_to_file


def run(config: Config):
    clear_or_create_folder(config.inputpath)
    clear_or_create_folder(config.temppath)
    # clear_or_create_folder(config.outputpath)

    #####################################################################
    # Step 0: Fetch available PO files and convert to JSON
    #####################################################################

    step_config, _ = get_step_config(config, "translation")
    for lang in step_config.languages:
        lang_code = lang["code"]
        translations_input_folder = Path(config.inputpath) / "translation" / lang_code
        translations_temp_folder = Path(config.temppath) / "translation" / lang_code

        if os.path.exists(translations_input_folder):
            shutil.rmtree(translations_input_folder)

        os.makedirs(translations_input_folder)
        os.makedirs(translations_temp_folder)

        # Download relevant PO translation files from github to temp folder
        language_folder_in_repo = step_config.folder_within_repo + "/" + lang_code
        translation_temp_po_folder = os.path.join(translations_temp_folder, "raw_po_files")
        download_translations_github(
            step_config.translation_repo,
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

    print("Fetched all available translations and converted to json")

    # Download all sheets used for flow creation and edits and store as json
    for step_identifier in ["create_flows", "edits_pretranslation", "edits_posttranslation"]:
        step_config, step_input_path = get_step_config(config, step_identifier, makedirs=True)

        spreadsheet_ids = step_config.spreadsheet_ids
        jsons = {}
        if step_config.archive is not None:
            archive_filepath = download_archive(config, step_config)
            with tempfile.TemporaryDirectory() as temp_dir:
                shutil.unpack_archive(archive_filepath, temp_dir)
                for sheet_id in spreadsheet_ids:
                    csv_folder = os.path.join(temp_dir, sheet_id)
                    jsons[sheet_id] = convert_to_json([csv_folder], "csv")
        else:
            for sheet_id in spreadsheet_ids:
                jsons[sheet_id] = convert_to_json(sheet_id, "google_sheets")
        for sheet_id, content in jsons.items():
            with open(step_input_path / f"{sheet_id}.json", "w") as export:
                export.write(content)

    print("Download of flow creation and edit sheets complete")

    # Postprocessing files
    step_config, step_input_path = get_step_config(config, "postprocessing", makedirs=True)
    shutil.copyfile(step_config.special_expiration_file, step_input_path / "special_expiration.json")
    shutil.copyfile(step_config.select_phrases_file, step_input_path / "select_phrases.json")
    shutil.copyfile(step_config.special_words_file, step_input_path / "special_words.json")

    # Safeguarding files
    step_config, step_input_path = get_step_config(config, "safeguarding", makedirs=True)
    safeguarding_file_path = step_input_path / "safeguarding_words.json"
    if step_config.sources:
        process_keywords_to_file(step_config.sources, safeguarding_file_path)
    else:
        shutil.copyfile(step_config.filepath, safeguarding_file_path)

    print("Download of postprocessing and safeguarding files complete")

    print("DONE.")


def download_archive(config, step_config):
    location = step_config.archive

    if location and location.startswith("http"):
        response = requests.get(location)

        if response.ok:
            archive_destinationpath = os.path.join(config.temppath, location + ".zip")
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
