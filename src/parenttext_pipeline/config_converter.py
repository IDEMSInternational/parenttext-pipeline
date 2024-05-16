from parenttext_pipeline import pipeline_version


def convert_config(config):
    return {
        # I am assuming that the list of sources contains only one entry,
        # as that is what I have observed in practice.
        # In the original config, config["sources"][0]["crowdin_name"]
        # specifies the output filename of the .pot file that is produced to
        # uploaded to crowdin. This is ignored as the filename is hardcoded now.
        "meta": {
            "pipeline_version": pipeline_version(),
        },
        "parents": [],
        "flows_outputbasename": config["sources"][0].get("filename"),
        "output_split_number": config["sources"][0].get("split_no"),
        "sources": {
            "flow_definitions": {
                "format": "sheets",
                "subformat": "google_sheets",
                "files_list": config["sources"][0].get("spreadsheet_ids"),
                "files_archive": config["sources"][0].get("archive"),
            },
            "edits_pretranslation": {
                "format": "sheets",
                "subformat": "google_sheets",
                "files_list": [
                    config.get(sheet_name)
                    for sheet_name in ["ab_testing_sheet_id", "localisation_sheet_id"]
                    if config.get(sheet_name)
                ],
            },
            "edits_posttranslation": {
                "format": "sheets",
                "subformat": "google_sheets",
                "files_list": [
                    config.get(sheet_name)
                    for sheet_name in ["transl_edits_sheet_id", "eng_edits_sheet_id"]
                    if config.get(sheet_name)
                ],
            },
            "translation": {
                "format": "translation_repo",
                "translation_repo": config.get("translation_repo"),
                "folder_within_repo": config.get("folder_within_repo"),
                "languages": config.get("languages"),
            },
            "expiration_times": {
                "format": "json",
                "files_dict": {
                    "special_expiration_file": config.get("special_expiration"),
                },
            },
            "qr_treatment": {
                "format": "json",
                "files_dict": {
                    "select_phrases_file": config.get("select_phrases"),
                    "special_words_file": config.get("special_words"),
                },
            },
            "safeguarding": {
                "format": "safeguarding",
                "filepath": config.get("sg_path"),
                "sources": config.get("sg_sources"),
            },
        },
        "steps": [
            {
                "id": "create_flows",
                "type": "create_flows",
                "sources": ["flow_definitions"],
                "models_module": config.get("model"),
                "tags": config["sources"][0].get("tags"),
            },
            {
                "id": "update_expiration_times",
                "type": "update_expiration_times",
                "sources": ["expiration_times"],
                "default_expiration_time": config.get("default_expiration"),
            },
            {
                "id": "edits_pretranslation",
                "type": "edits",
                "sources": ["edits_pretranslation"],
            },
            {
                "id": "hasanyword_pretranslation",
                "type": "has_any_word_check",
            },
            {
                "id": "overall_integrity_check_pretranslation",
                "type": "overall_integrity_check",
            },
            {
                "id": "extract_texts_for_translators",
                "type": "extract_texts_for_translators",
            },
            {
                "id": "translation",
                "type": "translation",
                "sources": ["translation"],
                "languages": config.get("languages"),
            },
            {
                "id": "edits_posttranslation",
                "type": "edits",
                "sources": ["edits_posttranslation"],
            },
            {
                "id": "hasanyword_posttranslation",
                "type": "has_any_word_check",
            },
            {
                "id": "fix_arg_qr_translation",
                "type": "fix_arg_qr_translation",
            },
            {
                "id": "overall_integrity_check_posttranslation",
                "type": "overall_integrity_check",
            },
            {
                "id": "qr_treatment",
                "type": "qr_treatment",
                "sources": ["qr_treatment"],
                "qr_treatment": config.get("qr_treatment"),
                "count_threshold": config.get("count_threshold"),
                "length_threshold": config.get("length_threshold"),
                "add_selectors": config.get("add_selectors"),
            },
            {
                "id": "safeguarding",
                "type": "safeguarding",
                "sources": ["safeguarding"],
                "flow_uuid": config.get("sg_flow_id"),
                "flow_name": config.get("sg_flow_name"),
                "redirect_flow_names": config.get("redirect_flow_names"),
            },
        ],
    }
