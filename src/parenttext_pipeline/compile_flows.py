from parenttext_pipeline.common import clear_or_create_folder
from parenttext_pipeline import steps


def run(config):
    clear_or_create_folder(config.outputpath)
    clear_or_create_folder(config.temppath)

    input_file = None
    for step_num, step_config in enumerate(config.steps):
        output_file = apply_step(config, step_config, step_num + 1, input_file)
        print(f"Applied step {step_config.type}, result stored at {output_file}")
        input_file = output_file

    steps.split_rapidpro_json(config, output_file)
    print("Result written to output folder")


STEP_MAPPING = {
        "create_flows": steps.create_flows,
        "load_flows": steps.load_flows,
        "edits": steps.apply_edits, 
        "extract_texts_for_translators": steps.apply_extract_texts_for_translators, 
        "fix_arg_qr_translation": steps.apply_fix_arg_qr_translation, 
        "has_any_word_check": steps.apply_has_any_word_check, 
        "overall_integrity_check": steps.apply_overall_integrity_check, 
        "qr_treatment": steps.apply_qr_treatment, 
        "safeguarding": steps.apply_safeguarding, 
        "translation": steps.apply_translations, 
        "update_expiration_times": steps.update_expiration_times,
    }


def apply_step(config, step_config, step_number, step_input_file):
    step_type = step_config.type
    function = STEP_MAPPING[step_type]
    step_output_file = function(config, step_config, step_number, step_input_file)
    if step_output_file is not None:
        return step_output_file
    return step_input_file
