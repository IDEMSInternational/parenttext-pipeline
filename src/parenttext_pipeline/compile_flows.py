from parenttext_pipeline.common import clear_or_create_folder, Config
from parenttext_pipeline import steps


def run(config: Config):
    clear_or_create_folder(config.outputpath)
    clear_or_create_folder(config.temppath)

    # step_output_file = steps.make_output_filepath(config, "_1_1_load_from_sheets.json")

    step_output_file = steps.create_flows(config)
    print(f"RapidPro flows created, file={step_output_file}")

    step_output_file = steps.update_expiration_time(config, "postprocessing", "1_1", step_output_file)
    print(f"Expiration_times_updated, file={step_output_file}")

    step_output_file = steps.apply_edits(config, "edits_pretranslation", 2, step_output_file)
    print(f"Applied pre-translation edits and A/B tests, file={step_output_file}")

    ####################################################################
    # Step 3: Catch errors pre-translation
    ####################################################################

    step_output_file = steps.apply_has_any_word_check(config, "hasanyword_pretranslation", "3_1", step_output_file)
    print(f"Applied pre-translation has_any_word checks, file={step_output_file}")

    step_output_file = steps.apply_overall_integrity_check(config, "overall_integrity_check_pretranslation", "3_2", step_output_file)
    print(f"Applied pre-translation overall_integrity_check, file={step_output_file}")

    #####################################################################
    # Step 4: Extract Text to send to translators
    #####################################################################

    step_output_file = steps.apply_extract_texts_for_translators(config, "extract_texts_for_translators", "4", step_output_file)
    print(f"Applied extract_texts_for_translators, file={step_output_file}")

    #####################################################################
    # Step 5: Localise translations back into JSON files
    #####################################################################

    step_output_file = steps.apply_translations(config, "translation", 5, step_output_file)
    print(f"Applied translations, file={step_output_file}")

    #####################################################################
    # step 6: post translation edits
    #####################################################################

    step_output_file = steps.apply_edits(config, "edits_posttranslation", 6, step_output_file)
    print(f"Applied post-translation edits and A/B tests, file={step_output_file}")

    #####################################################################
    # step 7: catch errors post translation
    #####################################################################

    step_output_file = steps.apply_has_any_word_check(config, "hasanyword_posttranslation", "7_1", step_output_file)
    print(f"Applied post-translation has_any_word checks, file={step_output_file}")

    step_output_file = steps.apply_fix_arg_qr_translation(config, "fix_arg_qr_translation", "7_2", step_output_file)
    print(f"Applied fix_arg_qr_translation, file={step_output_file}")

    step_output_file = steps.apply_overall_integrity_check(config, "overall_integrity_check_posttranslation", "7_3", step_output_file)
    print(f"Applied post-translation overall_integrity_check, file={step_output_file}")

    #####################################################################
    # step 8: add quick replies to message text and translation
    #####################################################################

    step_output_file = steps.apply_qr_treatment(config, "postprocessing", 8, step_output_file)
    print(f"Applied qr_treatment, file={step_output_file}")

    #####################################################################
    # step 9: implement safeguarding
    #####################################################################

    step_output_file = steps.apply_safeguarding(config, "safeguarding", 9, step_output_file)
    print(f"Applied safeguarding, file={step_output_file}")

    #####################################################################
    # step 10. split files (if too big)?
    #####################################################################

    steps.split_rapidpro_json(config, step_output_file)
    print("Result written to output folder")
