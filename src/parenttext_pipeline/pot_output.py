import os
import traceback
from parenttext_pipeline import steps
from parenttext_pipeline.common import (
    clear_or_create_folder,
    get_input_folder,
    read_meta,
    write_meta,
)
from parenttext_pipeline.compile_sources import compile_sources
from parenttext_pipeline.compile_flows import apply_step
from parenttext_pipeline.configs import CreateFlowsStepConfig


def run(config):
    clear_or_create_folder(config.outputpath)
    clear_or_create_folder(config.temppath)

    print("Compiling .pot files...")
    config.sources = compile_sources(".", get_input_folder(config))

    data = read_meta(config.inputpath)
    meta = {"pull_timestamp": data["pull_timestamp"]}
    write_meta(config, meta, config.outputpath)

    failed_groups = []
    
    for group_name, group_tags in po_output_groups.items():

        # Generate Override Steps Input Dict
        step = {
            "id": "create_flows",
            "type": "create_flows",
            "models_module": "models.parenttext_models",
            "sources": ["flow_definitions"],
            "tags": []
        }
        step['tags'] = group_tags

        # Apply new step
        config.steps[0] = CreateFlowsStepConfig(**step)

        # Run steps using code from compile_flows.py
        try:
            input_file = None
            for step_num, step_config in enumerate(config.steps):
                output_file = apply_step(config, step_config, step_num + 1, input_file)
                print(f"Applied step {step_config.type}, result stored at {output_file}")
                input_file = output_file

            steps.split_rapidpro_json(config, output_file)
            print("Result written to output folder")
            steps.write_diffable(config, output_file)
            print("Diffable written to output folder")
        except Exception as e:
            print(e)
            # store traceback string
            traceback_string = traceback.format_exc()
        
        try:
            # Move to the correct file
            translator_output_folder = os.path.join(config.outputpath, "send_to_translators")
            current_file = os.path.join(
                translator_output_folder, f"{config.flows_outputbasename}_crowdin.pot"
            )
            new_file = os.path.join(
                translator_output_folder, f"{config.sources['translation'].languages[0]['language']}_{group_name}.pot"
            )
            os.rename(current_file, new_file)
        except FileNotFoundError:
            failed_groups.append(group_name)
            # If the translate files were not produced, print out the error for why
            print(traceback_string)

    print(f'Failed Groups: {failed_groups}')


po_output_groups = {
    "modules":  [1, "module"],
    "activities": [1, "ltp_activity"],
    "onboarding": [1, "onboarding"],
    "survey": [1, "survey"],
    "navigation": [1, "delivery", 1,"menu", 1, "safeguarding"],
}