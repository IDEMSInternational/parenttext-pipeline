import os
import subprocess
import sys
from rapidpro_flow_tools import flow_converter

def main(credentials = None, token = None):

    sources = [
    {"filename": "srh_registration", "spreadsheet_id": "1yett-Rfzb9Ou8IQ1kwtrKPN_auhM-lk66r9gkqNV1As"},
    {"filename": "srh_entry", "spreadsheet_id": "19xvYfwWKA1hT5filGPWYEobQL1ZFfcFbTj1-aJCN8OQ"},
    {"filename": "srh_content", "spreadsheet_id": "1hOlgdqjmXZgl51L1olt357Gfiw2zRHNEl98aYTf8Hwo"},
    {"filename": "srh_safeguarding", "spreadsheet_id": "1A_p3cb3KNgX8XxD9MlCIoa294Y4Pb9obUKfwIvERALY"}
    ]

    for source in sources:

        source_file_name = source["filename"]
        spreadsheet_id  = source["spreadsheet_id"]

        if not os.path.exists("./output/"):
            os.makedirs("./output/")

        output_flow_path = "./output/" + source_file_name + ".json"
        flow_converter.convert_flow("create_flows", spreadsheet_id, output_flow_path, "google_sheets", "models.srh_models", credentials, token)
        
        print("created " + source_file_name)
        input_path = "./output/" + source_file_name + ".json"

        # # step 2: flow edits & A/B testing
        # SPREADSHEET_ID = "17q1mSyZU9Eu9-oHTE5zg20qrkkngfTlbgxjo2hOia_Q"
        # JSON_FILENAME = "..\\srh-jamaica-chatbot\\flows\\" + source_file_name + ".json"
        # source_file_name = source_file_name + "_avatar"
        # CONFIG_ab = "..\\srh-jamaica-chatbot\\edits\\ab_config.json"
        # output_path_2 = "temp\\" + source_file_name + ".json"
        # AB_log = "..\\srh-jamaica-chatbot\\temp\\AB_warnings.log"
        # os.chdir("..\\rapidpro_abtesting")
        # subprocess.run(["python", "main.py", JSON_FILENAME, "..\\srh-jamaica-chatbot\\" + output_path_2, SPREADSHEET_ID, "--format", "google_sheets", "--logfile", AB_log, "--config=" + CONFIG_ab])
        # print("added A/B tests and localisation")
        # input_path = output_path_2
        # os.chdir("..\\srh-jamaica-chatbot")

        # step 4: add quick replies to message text and translation
        source_file_name = source_file_name + "_no_QR"
        select_phrases_file = "./edits/select_phrases.json"
        special_words = "./edits/special_words.json"
        add_selectors = "yes"
        output_path_4 = "./output/"
        output_name_4 = source_file_name

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "move_quick_replies", input_path, select_phrases_file, output_name_4, output_path_4, add_selectors, special_words])
        print("Removed quick replies")

        # # step 5: safeguarding
        sg_flow_uuid = "ecbd9a63-0139-4939-8b76-343543eccd94"
        sg_flow_name = "SRH - Safeguarding - WFR interaction"
        
        input_path_5 = output_path_4 + output_name_4 + ".json"
        source_file_name = f"{source_file_name}_safeguarding"
        output_path_5 = f"./output/{source_file_name}.json"
        safeguarding_path = "./edits/safeguarding_srh.json"
        subprocess.run(["node", "./node_modules/@idems/safeguarding-rapidpro/srh_add_safeguarding_to_flows.js", input_path_5, safeguarding_path, output_path_5, sg_flow_uuid, sg_flow_name])
        print("Added safeguarding")

        if "srh_safeguarding" in source_file_name:
            subprocess.run(["node", "./node_modules/@idems/safeguarding-rapidpro/srh_edit_redirect_flow.js", output_path_5, safeguarding_path, output_path_5])
            print("Edited redirect sg flow")

        # # step final: split in 2 json files because it's too heavy to load (need to replace wrong flow names)
        if "srh_content" in source_file_name:
            input_path_6 = output_path_5
            n_file = 2
            subprocess.run(["node", "./node_modules/@idems/idems-chatbot-tools/split_in_multiple_json_files.js", input_path_6, str(n_file)])

            print(f"Split file in {n_file}")

if __name__ == '__main__':
    credentials = os.getenv('CREDENTIALS')
    token = os.getenv('TOKEN')
    main(credentials, token)

