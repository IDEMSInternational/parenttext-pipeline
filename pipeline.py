import os
import subprocess
import sys
from rapidpro_flow_tools import flow_converter
from config import *

def main(credentials = None, token = None):

    for source in sources:

        #Load core file information

        source_file_name = source["filename"]
        spreadsheet_id  = source["spreadsheet_id"]
        crowdin_file_name = source["crowdin_name"]

        #Setup output and temp files to store intermediary JSON files and log files
        if not os.path.exists("./output/"):
            os.makedirs("./output/")

        if not os.path.exists("./temp/"):
            os.makedirs("./temp/")

        #####################################################################
        #Step 1: Load google sheets and convert to RapidPro JSON
        #####################################################################

        output_file_name_1 = source_file_name + "_1"
        output_path_1 = "./output/" + output_file_name_1 + ".json"

        flow_converter.convert_flow("create_flows", spreadsheet_id, output_path_1, "google_sheets", "models.parenttext_models", credentials, token)
        
        print("Step 1 complete, created " + output_file_name_1)

        #####################################################################
        # Step 2: Flow edits (for all deployments) and localization (changes specific to a deployment)
        #####################################################################

        input_path_2 = "../parenttext-pipeline/output/" + output_file_name_1 + ".json"
        output_file_name_2 = source_file_name + "_2"
        output_path_2 = "../parenttext-pipeline/output/" + output_file_name_2 + ".json"
        AB_log = "../parenttext-pipeline/temp/2_AB_warnings.log"

        subprocess.run([
            "python", "-m", "rapidpro_abtesting.main",
            input_path_2, output_path_2, ab_testing_sheet_ID,
            "--format", "google_sheets",
            "--logfile", AB_log
        ])
        os.chdir("../parenttext-pipeline")
        
        print("Step 2 complete, added A/B tests and localization")        

        # Fix issues with _ui ?????not working?????
        # subprocess.run(["node", "./node_modules/@idems/idems-chatbot-tools/fix_ui.js", output_path_2, output_path_2])
        # print("Fixed _ui")

        #####################################################################
        # Step 3: Catch errors pre-translation
        #####################################################################

        input_path_3_1 = "./output/" +  output_file_name_2 + ".json"
        output_file_name_3_1 = source_file_name + "_3_1"
        has_any_words_log = "3_has_any_words_check"

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "has_any_words_check", input_path_3_1, "./output", output_file_name_3_1,  has_any_words_log])

        input_path_3_2 = "./output/" +  output_file_name_3_1 + ".json"
        integrity_log = "3_integrity_log"
        excel_log_name = "./temp/3_excel_log.xlsx"
        
        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "overall_integrity_check", input_path_3_2, "./output", integrity_log, excel_log_name])

        print("Step 3 complete, reviewed files pre-translation")

        #####################################################################
        # Step 4: Extract Text to send to translators
        #####################################################################


        #####################################################################
        # Step 5: Fetch PO files and convert to JSON
        #####################################################################
        
        output_translation_folder_5 = "./temp/"
        
        for lang in languages:

            lang_code = lang["code"]

            # Get PO files from the translation repo and merge them into a single JSON
            transl_repo = "../PLH-Digital-Content/translations/parent_text_v2/" + lang_code + "/"
            intern_transl = transl_repo + lang_code + "_" + crowdin_file_name + ".po"
            json_intern_transl = output_translation_folder_5 + lang_code + "_" + crowdin_file_name + ".json"
            subprocess.run(["node", "../idems_translation/common_tools/index.js", "convert", intern_transl, json_intern_transl])

        print("Step 5 complete, fetched translations and converted to json")

        #####################################################################
        # Step 6: Localise translations back into JSON files
        #####################################################################
        
        input_path_6 = "./output/" +  output_file_name_3_1 + ".json"
        output_file_name_6 = source_file_name + "_6"
        output_folder_6 = "./output/"

        for lang in languages:

            language = lang["language"]
            lang_code = lang["code"]

            json_intern_transl = output_translation_folder_5 + lang_code + "_" + crowdin_file_name + ".json"

            subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "localize", input_path_6, json_intern_transl, language, output_file_name_6, output_folder_6])

        print("Step 6 complete, localised translations back into JSON")

        #####################################################################
        # step 7: text & translation edits for dictionaries
        #####################################################################

        #####################################################################
        # step 8: catch errors post translation 
        #####################################################################

        input_path_8_1 = "./output/" +  output_file_name_6 + ".json"
        output_file_name_8_1 = source_file_name + "_8_1"
        has_any_words_log = "8_has_any_words_check"

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "has_any_words_check", input_path_8_1, "./output", output_file_name_8_1,  has_any_words_log])

        input_path_8_2 = "./output/" +  output_file_name_8_1 + ".json"
        output_file_name_8_2 = source_file_name + "_8_2"
        fix_arg_qr_log = "8_arg_qr_log"
        
        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "fix_arg_qr_translation", input_path_8_2, "./output", output_file_name_8_2, fix_arg_qr_log])

        input_path_8_3 = "./output/" +  output_file_name_8_2 + ".json"
        integrity_log = "8_integrity_log"
        excel_log_name = "./temp/8_excel_log.xlsx"
        
        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "overall_integrity_check", input_path_8_3, "./output", integrity_log, excel_log_name])

        print("Step 8 complete, reviewed files post translation")

        #####################################################################
        # step 9: add quick replies to message text and translation
        #####################################################################

        input_path_9 = "./output/" +  output_file_name_8_2 + ".json"
        select_phrases_file = "./edits/select_phrases.json"
        special_words = "./edits/special_words.json"
        add_selectors = "yes"
        output_path_9 = "./output/"
        output_file_name_9 = source_file_name + "_9"

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "move_quick_replies", input_path_9, select_phrases_file, output_file_name_9, output_path_9, add_selectors, special_words])
        
        print("Step 9 complete, removed quick replies")

        #####################################################################
        # step 9: safeguarding
        #####################################################################

        # # # step 5: safeguarding
        # sg_flow_uuid = "ecbd9a63-0139-4939-8b76-343543eccd94"
        # sg_flow_name = "SRH - Safeguarding - WFR interaction"
        
        # input_path_5 = output_path_4 + output_name_4 + ".json"
        # source_file_name = f"{source_file_name}_safeguarding"
        # output_path_5 = f"./output/{source_file_name}.json"
        # safeguarding_path = "./edits/safeguarding_srh.json"
        # subprocess.run(["node", "./node_modules/@idems/safeguarding-rapidpro/srh_add_safeguarding_to_flows.js", input_path_5, safeguarding_path, output_path_5, sg_flow_uuid, sg_flow_name])
        # print("Added safeguarding")

        # if "srh_safeguarding" in source_file_name:
        #     subprocess.run(["node", "./node_modules/@idems/safeguarding-rapidpro/srh_edit_redirect_flow.js", output_path_5, safeguarding_path, output_path_5])
        #     print("Edited redirect sg flow")

        #####################################################################
        # step 10. split files (if too big)?
        #####################################################################

        # # # step final: split in 2 json files because it's too heavy to load (need to replace wrong flow names)
        # if "srh_content" in source_file_name:
        #     input_path_6 = output_path_5
        #     n_file = 2
        #     subprocess.run(["node", "./node_modules/@idems/idems-chatbot-tools/split_in_multiple_json_files.js", input_path_6, str(n_file)])

        #     print(f"Split file in {n_file}")

if __name__ == '__main__':
    credentials = os.getenv('CREDENTIALS')
    token = os.getenv('TOKEN')
    main(credentials, token)

