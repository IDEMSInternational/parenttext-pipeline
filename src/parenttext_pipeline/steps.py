import json
import os
from copy import copy
from pathlib import Path
import shutil

from rapidpro_abtesting.main import apply_abtests
import rpft.converters
from rpft.logger.logger import initialize_main_logger
from parenttext_pipeline.common import get_step_config, run_node
from parenttext_pipeline.extract_keywords import batch



def input_files_from_ids(step_input_path, spreadsheet_ids):
    sheets = [
        os.path.join(step_input_path, f"{sheet_id}.json")
        for sheet_id in spreadsheet_ids
    ]
    return sheets


def make_output_filepath(config, suffix):
    return os.path.join(
        config.temppath,
        config.flows_outputbasename + suffix,
    )


def create_flows(config):
    step_config, step_input_path = get_step_config(config, "create_flows")
    step_output_file = make_output_filepath(config, "_1_1_load_from_sheets.json")

    sheets = input_files_from_ids(step_input_path, step_config.spreadsheet_ids)

    initialize_main_logger(Path(config.temppath) / "rpft.log")
    flows = rpft.converters.create_flows(
        sheets,
        None,
        "json",
        data_models=step_config.models_module,
        tags=step_config.tags,
    )
    with open(step_output_file, "w") as export:
        json.dump(flows, export, indent=4)

    return step_output_file


def apply_edits(config, step_name, step_number, step_input_file):
    step_config, step_input_path = get_step_config(config, step_name)
    input_sheets = input_files_from_ids(step_input_path, step_config.spreadsheet_ids)
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")
    log_file_path = os.path.join(config.temppath, f"{step_name}.log")

    apply_abtests(
        step_input_file,
        step_output_file,
        input_sheets,
        sheet_format="json",
        logfile=log_file_path,
    )

    return step_output_file


def apply_qr_treatment(config, step_name, step_number, step_input_file):
    step_config, _ = get_step_config(config, step_name)
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")
    # This is redundant, and we should change the JS script to just take the output filename
    # instead of step_output_basename and config.temppath as arguments
    step_output_basename = f"{config.flows_outputbasename}_{step_number}_{step_name}"

    # We can do different things to our quick replies depending on the deployment
    # channel
    if step_config.qr_treatment == "move":
        run_node(
            "idems_translation_chatbot/index.js",
            "move_quick_replies",
            step_input_file,
            step_config.select_phrases_file,
            step_output_basename,
            config.temppath,
            step_config.add_selectors,
            str(step_config.qr_limit),
            step_config.special_words_file,
        )
        print("Step 8 complete, removed quick replies")
    elif step_config.qr_treatment == "move_and_mod":
        run_node(
            "idems_translation_chatbot/index.js",
            "move_and_mod_quick_replies",
            step_input_file,
            step_config.select_phrases_file,
            step_config.replace_phrases,
            step_output_basename,
            config.temppath,
            step_config.add_selectors,
            str(step_config.qr_limit),
            step_config.special_words_file,
        )
        print("Step 8 complete, removed and modified quick replies")
    elif step_config.qr_treatment == "reformat":
        run_node(
            "idems_translation_chatbot/index.js",
            "reformat_quick_replies",
            step_input_file,
            step_config.select_phrases_file,
            step_output_basename,
            config.temppath,
            step_config.count_threshold,
            step_config.length_threshold,
            str(step_config.qr_limit),
            step_config.special_words_file,
        )
        print("Step 8 complete, reformatted quick replies")
    elif step_config.qr_treatment == "reformat_china":
        run_node(
            "idems_translation_chatbot/index.js",
            "reformat_quick_replies_china",
            step_input_file,
            step_config.select_phrases_file,
            step_output_basename,
            config.temppath,
            step_config.count_threshold,
            step_config.length_threshold,
            str(step_config.qr_limit),
            step_config.special_words_file,
        )
        print("Step 8 complete, reformatted quick replies to China standard")
    elif step_config.qr_treatment == "wechat":
        run_node(
            "idems_translation_chatbot/index.js",
            "convert_qr_to_html",
            step_input_file,
            step_output_basename,
            config.temppath
        )
        print("Step 8 complete, moved quick replies to html")
    else:
        step_output_file = step_input_file
        print("Step 8 skipped, no QR edits specified")

    return step_output_file


def apply_safeguarding(config, step_name, step_number, step_input_file):
    step_config, step_input_path = get_step_config(config, step_name)
    safeguarding_file_path = step_input_path / "safeguarding_words.json"
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")

    # We may apply both of these operations.
    if step_config.flow_name and step_config.flow_uuid:
        run_node(
            "safeguarding-rapidpro/v2_add_safeguarding_to_flows.js",
            step_input_file,
            str(safeguarding_file_path),
            step_output_file,
            step_config.flow_uuid,
            step_config.flow_name,
        )
        step_input_file = step_output_file
        print("Safeguarding flows added")

    if step_config.redirect_flow_names:
        run_node(
            "safeguarding-rapidpro/v2_edit_redirect_flow.js",
            step_input_file,
            str(safeguarding_file_path),
            step_output_file,
            step_config.redirect_flow_names,
        )
        print("Redirect flows edited")

    return step_output_file


def apply_translations(config, step_name, step_number, step_input_file):
    step_config, _ = get_step_config(config, step_name)
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")
    # This is redundant, and we should change the JS script to just take the output filename
    # instead of step_output_basename and config.temppath as arguments
    step_output_basename = f"{config.flows_outputbasename}_{step_number}_{step_name}"

    merge_translation_jsons(config, step_name)

    for lang in step_config.languages:
        json_translation_path = os.path.join(
            config.temppath, step_name, lang["code"], "merged_translations.json"
        )

        run_node(
            "idems_translation_chatbot/index.js",
            "localize",
            step_input_file,
            json_translation_path,
            lang["language"],
            step_output_basename,
            config.temppath,
        )

        step_input_file = step_output_file
    
    return step_output_file


def apply_has_any_word_check(config, step_name, step_number, step_input_file):
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")
    # This is redundant, and we should change the JS script to just take the output filename
    # instead of step_output_basename and config.temppath as arguments
    step_output_basename = f"{config.flows_outputbasename}_{step_number}_{step_name}"
    # This is inconsistent. Why not specify the output filename?
    has_any_words_log = f"{step_number}_{step_name}"

    run_node(
        "idems_translation_chatbot/index.js",
        "has_any_words_check",
        step_input_file,
        config.temppath,
        step_output_basename,
        has_any_words_log,
    )
    
    return step_output_file


def apply_overall_integrity_check(config, step_name, step_number, step_input_file):
    # Only log files are produced in this step.
    step_output_file = step_input_file
    # This is inconsistent. Why not specify the output filename?
    integrity_log = f"{step_number}_{step_name}"
    excel_log_name = os.path.join(config.temppath, f"{step_number}_{step_name}.xlsx")

    run_node(
        "idems_translation_chatbot/index.js",
        "overall_integrity_check",
        step_input_file,
        config.temppath,
        integrity_log,
        excel_log_name,
    )

    return step_output_file


def apply_fix_arg_qr_translation(config, step_name, step_number, step_input_file):
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")
    # This is redundant, and we should change the JS script to just take the output filename
    # instead of step_output_basename and config.temppath as arguments
    step_output_basename = f"{config.flows_outputbasename}_{step_number}_{step_name}"
    # This is inconsistent. Why not specify the output filename?
    fix_arg_qr_log = f"{step_number}_{step_name}"

    run_node(
        "idems_translation_chatbot/index.js",
        "fix_arg_qr_translation",
        step_input_file,
        config.temppath,
        step_output_basename,
        fix_arg_qr_log,
    )

    return step_output_file


def apply_extract_texts_for_translators(config, step_name, step_number, step_input_file):
    # Only translation files are produced in this step.
    step_output_file = step_input_file
    # This is redundant, and we should change the JS script to just take the output filename
    # instead of step_output_basename and config.temppath as arguments
    step_translation_basename = f"{config.flows_outputbasename}_{step_number}_{step_name}"
    step_translation_file = os.path.join(config.temppath, step_translation_basename + ".json")

    # Setup output file to send to translators if it doesn't exist
    translator_output_folder = os.path.join(config.outputpath, "send_to_translators")
    if not os.path.exists(translator_output_folder):
        os.makedirs(translator_output_folder)
    translation_output_file = os.path.join(translator_output_folder, f"{config.flows_outputbasename}_crowdin.pot")

    # Produce translatable strings in json format
    run_node(
        "idems_translation_chatbot/index.js",
        "extract_simple",
        step_input_file,
        config.temppath,
        step_translation_basename,
    )

    # Convert to pot
    run_node(
        "idems_translation_common/index.js",
        "convert",
        step_translation_file,
        translation_output_file,
    )

    return step_output_file


def merge_translation_jsons(config, step_name):
    step_config, _ = get_step_config(config, step_name)
    for lang in step_config.languages:
        translations_input_folder = Path(config.inputpath) / step_name / lang["code"]
        translations_temp_folder = Path(config.temppath) / step_name / lang["code"]
        os.makedirs(translations_temp_folder, exist_ok=True)

        # Merge all translation files into a single JSON that we can localise back into
        # our flows
        run_node(
            "idems_translation_common/index.js",
            "concatenate_json",
            translations_input_folder,
            translations_temp_folder,
            "merged_translations.json",
        )


def update_expiration_time(config, step_name, step_number, step_input_file):
    step_config, step_input_path = get_step_config(config, step_name)
    step_output_file = make_output_filepath(config, f"_{step_number}_{step_name}.json")
    special_expiration_filepath = os.path.join(step_input_path, "special_expiration.json")

    with open(special_expiration_filepath, "r") as specifics_json:
        specifics = json.load(specifics_json)

    with open(step_input_file, "r") as in_json:
        org = json.load(in_json)

    for flow in org.get("flows", []):
        set_expiration(flow, step_config.default_expiration_time, specifics)

    with open(step_output_file, "w") as out_json:
        json.dump(org, out_json)

    return step_output_file


def set_expiration(flow, default, specifics={}):
    expiration = specifics.get(flow["name"], default)

    flow["expire_after_minutes"] = expiration

    if "expires" in flow.get("metadata", {}):
        flow["metadata"]["expires"] = expiration

    return flow


def split_rapidpro_json(config, input_filename):
    n = config.output_split_number
    assert isinstance(n, int) and n >= 1
    if n == 1:
        output_filename = Path(config.outputpath) / f"{config.flows_outputbasename}.json"
        shutil.copyfile(input_filename, output_filename)
        return

    with open(input_filename, 'r', encoding='utf-8') as in_json:
        org = json.load(in_json)

    flows_per_file = len(org["flows"]) // n

    for i, b in enumerate(batch(org["flows"], flows_per_file), start=1):
        org_new = copy(org)
        org_new.update(
            {
                "campaigns": [
                    edited
                    for campaign in org["campaigns"]
                    if (edited := edit_campaign(campaign, b))
                ],
                "flows": b,
                "triggers": [
                    trigger
                    for trigger in org["triggers"]
                    if trigger["flow"]["uuid"] in [flow["uuid"] for flow in b]
                ],
            }
        )
        output_filename = Path(config.outputpath) / f"{config.flows_outputbasename}_{i}.json"

        with open(output_filename, "w") as out_file:
            json.dump(org_new, out_file, indent=2)
            print(f"File written, path={output_filename}")


def edit_campaign(campaign, flows):
    if not campaign["events"]:
        return campaign

    campaign_new = copy(campaign)
    campaign_new["events"] = []
    for event in campaign["events"]:
        event_type = event["event_type"]
        flow_name = event["flow"]["name"]
        if event_type in ["F", "M"] and flow_name in [f["name"] for f in flows]:
            campaign_new["events"].append(event)
        else:
            print(
                f"Campaign event removed, campaign={campaign['name']}, "
                f"event_type={event_type}"
            )
            if event_type == "F":
                print(f"Flow not found, name={flow_name}")

    if campaign_new["events"]:
        return campaign_new
