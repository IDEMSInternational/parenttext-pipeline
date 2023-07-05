import os
import subprocess
import sys
from rapidpro_flow_tools import flow_converter

def prepare_for_translations(sources, ab_testing_sheet_ID, outputpath, model, credentials = None, token = None):

    for source in sources:

        #Load core file information

        source_file_name = source["filename"]
        spreadsheet_id  = source["spreadsheet_id"]
        crowdin_file_name = source["crowdin_name"]

        #Setup output and temp files to store intermediary JSON files and log files
        if not os.path.exists(outputpath):
            os.makedirs(outputpath)

        #####################################################################
        #Step 1: Load google sheets and convert to RapidPro JSON
        #####################################################################

        #Step 1 currently skipped as not working, error on run is,
        #"ValueError: Field tag doesn't exist in target type <class 'parsers.creation.contentindexrowmodel.ContentIndexRowModel'>."
        #Believe this relates to the model file that we are feeding in being incomplete, parenttext_models.py maybe needs to be updated?

        output_file_name_1 = source_file_name + "_1"
        output_path_1 = os.path.join(outputpath, output_file_name_1 + ".json")

        # flow_converter.convert_flow("create_flows", spreadsheet_id, output_path_1, "google_sheets", model, credentials, token)
        
        # print("Step 1 complete, created " + output_file_name_1)

        #####################################################################
        # Step 2: Flow edits (for all deployments) and localization (changes specific to a deployment)
        #####################################################################

        #Step 2 currently skipped as not working, error on run is,
        #"C:\Users\edmun\AppData\Local\Programs\Python\Python311\python.exe: Error while finding module specification for 'rapidpro-abtesting.main' (ModuleNotFoundError: No module named 'rapidpro-abtesting')"
        #This is even when running from venv which displaces that it has "rapidpro-abtesting - 0.1.0" installed so not sure why it can't find it

        input_path_2 = output_path_1
        output_file_name_2 = source_file_name + "_2"
        output_path_2 = os.path.join(outputpath, output_file_name_2 + ".json")
        # AB_log = os.path.join(outputpath, "/2_AB_warnings.log")

        # subprocess.run([
        #     "python", "-m", "rapidpro-abtesting.main",
        #     input_path_2, output_path_2, ab_testing_sheet_ID,
        #     "--format", "google_sheets",
        #     "--logfile", AB_log
        # ])
        # print("Step 2 complete, added A/B tests and localization")        
 
        # Fix issues with _ui ?????not working?????
        # subprocess.run(["node", "./node_modules/@idems/idems-chatbot-tools/fix_ui.js", output_path_2, output_path_2])
        # print("Fixed _ui")

        ####################################################################
        # Step 3: Catch errors pre-translation
        ####################################################################

        input_path_3_1 = output_path_2
        output_file_name_3_1 = source_file_name + "_3_1"
        has_any_words_log = "3_has_any_words_check"

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "has_any_words_check", input_path_3_1, outputpath, output_file_name_3_1, has_any_words_log])

        input_path_3_2 = os.path.join(outputpath, output_file_name_3_1 + ".json")
        integrity_log = "3_integrity_log"
        excel_log_name = os.path.join(outputpath, "3_excel_log.xlsx")
        
        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "overall_integrity_check", input_path_3_2, outputpath, integrity_log, excel_log_name])

        print("Step 3 complete, reviewed files pre-translation")

        #####################################################################
        # Step 4: Extract Text to send to translators
        #####################################################################

        input_path_4 = os.path.join(outputpath, output_file_name_3_1 + ".json")
        output_file_name_4 = crowdin_file_name
        output_path_4 = os.path.join(outputpath, "send_to_translators")

        #Setup output file to send to translators if it doesn't exist
        if not os.path.exists(output_path_4):
            os.makedirs(output_path_4)

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "extract_simple", input_path_4, output_path_4, output_file_name_4])

        print("Step 4 complete, extracted text for translation")


def process_post_translation(sources, languages, translation_repo, outputpath, select_phrases, special_words, add_selectors):

    #####################################################################
    # Step 5: Fetch PO files and convert to JSON
    #####################################################################

    for lang in languages:

        lang_name = lang["language"]
        lang_code = lang["code"]

        #Setup file to store the translations we retrieve from the translation repo
        translations_store_folder = os.path.join(outputpath, lang_name + "_translations")
        if not os.path.exists(translations_store_folder):
            os.makedirs(translations_store_folder)

        #Fetch all relevant translation files
        translations_fetch_folder = os.path.join(translation_repo, lang_code)
        for root, dirs, files in os.walk(translations_fetch_folder):
            for file in files:
                file_name, file_extension = os.path.splitext(file)
                if file_extension == ".po":
                    source_file_path = os.path.join(root, file)
                    dest_file_path = os.path.join(translations_store_folder, file_name + ".json")
                    subprocess.run(["node", "./node_modules/@idems/idems_translation_common/index.js", "convert", source_file_path, dest_file_path])

        #Merge all translation files into a single JSON that we can localise back into our flows
        subprocess.run(["node", "./node_modules/@idems/idems_translation_common/index.js", "concatenate_json", translations_store_folder, translations_store_folder, "merged_translations.json"])

    print("Step 5 complete, fetched translations and converted to json")

    #####################################################################
    # Step 6: Localise translations back into JSON files
    #####################################################################

    for source in sources:

        #Load core file information

        source_file_name = source["filename"]

        #Setup output and temp files to store intermediary JSON files and log files
        if not os.path.exists(outputpath):
            os.makedirs(outputpath)
        
        input_path_6 = os.path.join(outputpath, source_file_name + "_3_1.json")
        output_file_name_6 = source_file_name + "_6"

        for lang in languages:

            language = lang["language"]

            json_translation_path = os.path.join(outputpath, language + "_translations", "merged_translations.json")

            subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "localize", input_path_6, json_translation_path, language, output_file_name_6, outputpath])

        print("Step 6 complete, localised translations back into JSON")

        #####################################################################
        # step 7: text & translation edits for dictionaries
        #####################################################################

        ##add based on Chiara's draft pipeline

        #####################################################################
        # step 8: catch errors post translation 
        #####################################################################

        input_path_8_1 = os.path.join(outputpath, output_file_name_6 + ".json")
        output_file_name_8_1 = source_file_name + "_8_1"
        has_any_words_log = "8_has_any_words_check"

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "has_any_words_check", input_path_8_1, outputpath, output_file_name_8_1,  has_any_words_log])

        input_path_8_2 = os.path.join(outputpath, output_file_name_8_1 + ".json")
        output_file_name_8_2 = source_file_name + "_8_2"
        fix_arg_qr_log = "8_arg_qr_log"
        
        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "fix_arg_qr_translation", input_path_8_2, outputpath, output_file_name_8_2, fix_arg_qr_log])

        input_path_8_3 = os.path.join(outputpath, output_file_name_8_2 + ".json")
        integrity_log = "8_integrity_log"
        excel_log_name = os.path.join(outputpath,"8_excel_log.xlsx")
        
        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "overall_integrity_check", input_path_8_3, "./output", integrity_log, excel_log_name])

        print("Step 8 complete, reviewed files post translation")

        #####################################################################
        # step 9: add quick replies to message text and translation
        #####################################################################

        input_path_9 = os.path.join(outputpath, output_file_name_8_2 + ".json")
        output_file_name_9 = source_file_name + "_9"

        #changes to be made here aroud length of strings.

        subprocess.run(["node", "./node_modules/@idems/idems_translation_chatbot/index.js", "move_quick_replies", input_path_9, select_phrases, output_file_name_9, outputpath, add_selectors, special_words])
        
        print("Step 9 complete, removed quick replies")

        #####################################################################
        # step 10: implement safeguarding
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
        # step 11. split files (if too big)?
        #####################################################################

        # # # step final: split in 2 json files because it's too heavy to load (need to replace wrong flow names)
        # if "srh_content" in source_file_name:
        #     input_path_6 = output_path_5
        #     n_file = 2
        #     subprocess.run(["node", "./node_modules/@idems/idems-chatbot-tools/split_in_multiple_json_files.js", input_path_6, str(n_file)])

        #     print(f"Split file in {n_file}")

def process_safeguarding_words(input_file, output_path, output_name):

    #####################################################################
    #Fetch translated safeguarding words and turn into JSON
    #####################################################################

    #"./extract_keywords.py" has the rough script required to run this process, need to adapt as necessary

    print("Safeguarding word processing complete")