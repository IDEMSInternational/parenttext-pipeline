import json
import os
import requests
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rpft.converters import create_flows
from rpft.logger.logger import initialize_main_logger
from rapidpro_abtesting.main import apply_abtests

from parenttext_pipeline.steps import update_expiration_time, split_rapidpro_json


@dataclass(kw_only=True)
class Config:
    sources: list
    special_expiration: str
    default_expiration: int
    model: str
    languages: list
    translation_repo: str
    folder_within_repo: str
    outputpath: str = "output"
    qr_treatment: str
    select_phrases: str
    add_selectors: str
    special_words: str
    count_threshold: int
    length_threshold: int
    ab_testing_sheet_id: str = ""
    localisation_sheet_id: str = ""
    eng_edits_sheet_id: str = ""
    transl_edits_sheet_id: str = ""
    sg_flow_id: str = ""
    sg_flow_name: str = ""
    sg_path: str = ""
    redirect_flow_names: str = ""


def run(config: Config):
    outputpath = config.outputpath

    if not os.path.exists(outputpath):
        os.makedirs(outputpath)

    #####################################################################
    # Step 0: Fetch available PO files and convert to JSON
    #####################################################################

    for lang in config.languages:
        lang_name = lang["language"]
        lang_code = lang["code"]
        translations_store_folder = Path(outputpath) / f"{lang_name}_translations"

        if os.path.exists(translations_store_folder):
            shutil.rmtree(translations_store_folder)

        os.makedirs(translations_store_folder)

        # Download relevant translation files from github
        language_folder_in_repo = config.folder_within_repo + "/" + lang_code
        raw_translation_store = os.path.join(translations_store_folder, "raw_po_files")
        download_translations_github(
            config.translation_repo,
            language_folder_in_repo,
            raw_translation_store,
        )

        for root, dirs, files in os.walk(raw_translation_store):
            for file in files:
                file_name = Path(file).stem
                source_file_path = os.path.join(root, file)
                dest_file_path = os.path.join(
                    translations_store_folder,
                    file_name + ".json",
                )
                run_node(
                    "idems_translation_common/index.js",
                    "convert",
                    source_file_path,
                    dest_file_path,
                )

        # Merge all translation files into a single JSON that we can localise back into
        # our flows
        run_node(
            "idems_translation_common/index.js",
            "concatenate_json",
            translations_store_folder,
            translations_store_folder,
            "merged_translations.json",
        )

    print("Step 0 complete, fetched all available translations and converted to json")

    initialize_main_logger(Path(outputpath) / "rpft.log")

    for source in config.sources:
        source_file_name = source["filename"]
        crowdin_file_name = source["crowdin_name"]

        #####################################################################
        # Step 1: Load google sheets and convert to RapidPro JSON
        #####################################################################

        archive_fp = download_archive(config, source)
        input_path_1_2 = load_sheets(config, source, archive_fp)
        input_path_2 = update_expiration_time(config, source, input_path_1_2)

        print("Step 1 complete")

        #####################################################################
        # Step 2: Flow edits (for all deployments) and localization (changes specific to
        # a deployment)
        #####################################################################

        log_file_path = os.path.join(outputpath, "2_ab_testing.log")
        ab_testing_sheet_id = config.ab_testing_sheet_id
        localisation_sheet_id = config.localisation_sheet_id

        if ab_testing_sheet_id or localisation_sheet_id:
            output_file_name_2 = source_file_name + "_2_flow_edits"
            output_path_2 = os.path.join(outputpath, output_file_name_2 + ".json")

            input_sheets = [
                sheet
                for sheet in [config.ab_testing_sheet_id, config.localisation_sheet_id]
                if sheet
            ]

            apply_abtests(
                input_path_2,
                output_path_2,
                input_sheets,
                "google_sheets",
                log_file_path,
            )
            print("Step 2 complete, added A/B tests and localization")
        else:
            output_path_2 = input_path_2
            print("Step 2 skipped, no AB testing sheet ID provided")

        ####################################################################
        # Step 3: Catch errors pre-translation
        ####################################################################

        input_path_3_1 = output_path_2
        output_file_name_3_1 = source_file_name + "_3_1_has_any_word_check"
        has_any_words_log = "3_has_any_words_check"

        run_node(
            "idems_translation_chatbot/index.js",
            "has_any_words_check",
            input_path_3_1,
            outputpath,
            output_file_name_3_1,
            has_any_words_log,
        )

        input_path_3_2 = os.path.join(outputpath, output_file_name_3_1 + ".json")
        integrity_log = "3_integrity_log"
        excel_log_name = os.path.join(outputpath, "3_excel_log.xlsx")

        run_node(
            "idems_translation_chatbot/index.js",
            "overall_integrity_check",
            input_path_3_2,
            outputpath,
            integrity_log,
            excel_log_name,
        )

        print("Step 3 complete, reviewed files pre-translation")

        #####################################################################
        # Step 4: Extract Text to send to translators
        #####################################################################

        input_path_4_1 = input_path_3_2
        output_file_name_4_1 = source_file_name + "_4_english_for_translation"

        run_node(
            "idems_translation_chatbot/index.js",
            "extract_simple",
            input_path_4_1,
            outputpath,
            output_file_name_4_1,
        )

        translator_folder = os.path.join(outputpath, "send_to_translators")

        # Setup output file to send to translators if it doesn't exist
        if not os.path.exists(translator_folder):
            os.makedirs(translator_folder)

        input_path_4_2 = os.path.join(outputpath, output_file_name_4_1 + ".json")
        output_path_4_2 = os.path.join(translator_folder, crowdin_file_name + ".pot")

        run_node(
            "idems_translation_common/index.js",
            "convert",
            input_path_4_2,
            output_path_4_2,
        )

        print("Step 4 complete, extracted text for translation")

        #####################################################################
        # Step 5: Localise translations back into JSON files
        #####################################################################

        input_path_5 = input_path_3_2
        output_file_name_5 = source_file_name + "_5_localised_translations"

        for lang in config.languages:
            language = lang["language"]

            json_translation_path = os.path.join(
                outputpath, language + "_translations", "merged_translations.json"
            )

            run_node(
                "idems_translation_chatbot/index.js",
                "localize",
                input_path_5,
                json_translation_path,
                language,
                output_file_name_5,
                outputpath,
            )

            input_path_5 = os.path.join(outputpath, output_file_name_5 + ".json")

        print("Step 5 complete, localised translations back into JSON")

        #####################################################################
        # step 6: post translation edits
        #####################################################################

        input_path_6 = os.path.join(outputpath, output_file_name_5 + ".json")
        log_file_path = os.path.join(outputpath, "6_dict_edits.log")

        input_edit_sheets = [
            sheet
            for sheet in [config.eng_edits_sheet_id, config.transl_edits_sheet_id]
            if sheet
        ]

        if input_edit_sheets:
            output_file_name_6 = source_file_name + "_6_dict_edits"
            output_path_6 = os.path.join(outputpath, output_file_name_6 + ".json")

            apply_abtests(
                input_path_6,
                output_path_6,
                input_edit_sheets,
                "google_sheets",
                log_file_path,
            )
            print("Step 6 complete, text & translation edits made for dictionaries")
        else:
            output_path_6 = input_path_6
            print("Step 6 skipped, no dict edits sheet ID provided")

        #####################################################################
        # step 7: catch errors post translation
        #####################################################################

        input_path_7_1 = output_path_6
        output_file_name_7_1 = source_file_name + "_7_1_has_any_word_check"
        has_any_words_log = "7_has_any_words_check"

        run_node(
            "idems_translation_chatbot/index.js",
            "has_any_words_check",
            input_path_7_1,
            outputpath,
            output_file_name_7_1,
            has_any_words_log,
        )

        input_path_7_2 = os.path.join(outputpath, output_file_name_7_1 + ".json")
        output_file_name_7_2 = source_file_name + "_7_2_fix_arg_qr_translation"
        fix_arg_qr_log = "7_arg_qr_log"

        run_node(
            "idems_translation_chatbot/index.js",
            "fix_arg_qr_translation",
            input_path_7_2,
            outputpath,
            output_file_name_7_2,
            fix_arg_qr_log,
        )

        input_path_7_3 = os.path.join(outputpath, output_file_name_7_2 + ".json")
        integrity_log = "7_integrity_log"
        excel_log_name = os.path.join(outputpath, "8_excel_log.xlsx")

        run_node(
            "idems_translation_chatbot/index.js",
            "overall_integrity_check",
            input_path_7_3,
            outputpath,
            integrity_log,
            excel_log_name,
        )

        print("Step 7 complete, reviewed files post translation")

        #####################################################################
        # step 8: add quick replies to message text and translation
        #####################################################################

        input_path_8 = os.path.join(outputpath, output_file_name_7_2 + ".json")
        output_file_name_8 = source_file_name + "_8_modify_QR"

        # We can do different things to our quick replies depending on the deployment
        # channel
        if config.qr_treatment == "move":
            run_node(
                "idems_translation_chatbot/index.js",
                "move_quick_replies",
                input_path_8,
                config.select_phrases,
                output_file_name_8,
                outputpath,
                config.add_selectors,
                config.qr_limit,
                config.special_words,
            )
            output_path_8 = os.path.join(outputpath, output_file_name_8 + ".json")
            print("Step 8 complete, removed quick replies")
        elif config.qr_treatment == "reformat":
            run_node(
                "idems_translation_chatbot/index.js",
                "reformat_quick_replies",
                input_path_8,
                config.select_phrases,
                output_file_name_8,
                outputpath,
                config.count_threshold,
                config.length_threshold,
                config.qr_limit,
                config.special_words,
            )
            output_path_8 = os.path.join(outputpath, output_file_name_8 + ".json")
            print("Step 8 complete, reformatted quick replies")
        elif config.qr_treatment == "wechat":
            run_node(
                "idems_translation_chatbot/index.js",
                "convert_qr_to_html",
                input_path_8,
                output_file_name_8,
                outputpath
            )
            output_path_8 = os.path.join(outputpath, output_file_name_8 + ".json")
            print("Step 8 complete, reformatted quick replies")
        else:
            output_path_8 = input_path_8
            print("Step 8 skipped, no QR edits specified")

        #####################################################################
        # step 9: implement safeguarding
        #####################################################################

        input_path_9 = output_path_8

        if (
            config.sg_path
            and config.sg_flow_name
            and config.sg_flow_id
            and config.redirect_flow_names
        ):
            output_file_name_9 = source_file_name + "_9_safeguarding"
            output_path_9 = os.path.join(outputpath, output_file_name_9 + ".json")
            run_node(
                "safeguarding-rapidpro/v2_add_safeguarding_to_flows.js",
                input_path_9,
                config.sg_path,
                output_path_9,
                config.sg_flow_id,
                config.sg_flow_name,
            )

            run_node(
                "safeguarding-rapidpro/v2_edit_redirect_flow.js",
                output_path_9,
                config.sg_path,
                output_path_9,
                config.redirect_flow_names,
            )

            print(
                "Step 9 complete, adding safeguarding flows and edited redirect flows"
            )
        else:
            output_path_9 = input_path_9
            print("Step 9 skipped, no safeguarding details provided")

        #####################################################################
        # step 10. split files (if too big)?
        #####################################################################

        split_rapidpro_json(config, source, output_path_9)
        print("Step 10 completed")


def download_archive(config, source):
    location = source.get("archive")
    archive_fp = os.path.join(config.outputpath, source["filename"] + ".zip")

    if location and location.startswith("http"):
        response = requests.get(location)

        if response.ok:
            with open(archive_fp, "wb") as archive:
                archive.write(response.content)
            print(f"Archive downloaded, url={location}, file={archive_fp}")
        else:
            print(
                f"Archive download failed, "
                f"status={response.status_code}, url={location}"
            )

        return archive_fp
    else:
        return location


def load_sheets(config, source, archive_fp):
    output_path = os.path.join(
        config.outputpath,
        source["filename"] + "_1_1_load_from_sheets.json",
    )
    spreadsheet_ids = source["spreadsheet_ids"]
    tags = source["tags"]

    if archive_fp:
        with tempfile.TemporaryDirectory() as temp_dir:
            shutil.unpack_archive(archive_fp, temp_dir)
            flows = create_flows(
                [
                    os.path.join(temp_dir, spreadsheet_id)
                    for spreadsheet_id in spreadsheet_ids
                ],
                None,
                "csv",
                data_models=config.model,
                tags=tags,
            )
    else:
        flows = create_flows(
            spreadsheet_ids,
            None,
            "google_sheets",
            data_models=config.model,
            tags=tags,
        )

    with open(output_path, "w") as export:
        json.dump(flows, export, indent=4)

    print(f"RapidPro flows created, file={output_path}")

    return output_path


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


def run_node(script, *args):
    subprocess.run(["node", "node_modules/@idems/" + script, *args])
