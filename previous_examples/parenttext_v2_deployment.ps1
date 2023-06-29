################################
#step 0: create flows
################################
Set-Location "..\rapidpro-flow-toolkit"


$T_C_onboarding_ID = "12ddvTz_ZfC-9-b0yxjVrSzczciUUE3GosLUFeOLIv9I"
$T_content_ID = "1hcH8pFdiHZN0UvZgyv3Zht9ARBTx-VXhNBI2o8L7fHU" #multiple content index for different types of content
$C_ltp_activities_ID = "1Jx7vOmdefzK62ao2nlJJVLMAIS8d-6r1G8qn0jG8gww"
$T_delivery_ID = "1yf6T8FsNF5SIS7ktj05Wj7ha_Hkfrf66r63kfUWhJbI"
$C_modules_teen_ID = "1ONmD9PF9rcno3ha3QpfrIR5EIvHuuEqJXF3T90rlZ78"
$C_dictionaries_ID = "1uc4WOOlyHTEV8fUGb8nPCYcPj446TRtsV8fucrOCxC4"
$C_home_activity_checkin_ID = "1qjjM2XfkvGVk38GL2OASNkTrXyXuDMAuMUAKmgHYt_s"
$T_C_menu_ID = "1lf80mIiuv_F6xAa9j5zGvXas50WxdSsLj6vrPccGNwY"
$C_goal_checkin_ID = "1gympuD5KdlAdDJSuaVQiXjWSwJxoDcA9K-oBRyKmS7o"
$C_dev_asess_tool_ID = "1OhhQF5yarUDmaSl2tlt7eIT7wJ8bGwNFzI3BOplJYsc"
$C_malaysia_demo_ID = "1Fi1r42n5dg4yyPXWLWqS72QwpdKHVuvtvIBJT6fYOFQ"

#home activity checkin
python main.py create_flows $T_content_ID $C_home_activity_checkin_ID  -o "..\parenttext-version-2\flows\parenttext_homeactivitycheckin.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_homeactivitycheckin"
$crowdin_file_name = "home_activity_checkin_teen"  
<#
#onboarding
python main.py create_flows $T_C_onboarding_ID -o "..\parenttext-version-2\flows\parenttext_onboarding.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_onboarding"

#delivery with activity 
python main.py create_flows $C_ltp_activities_ID $T_delivery_ID $C_modules_teen_ID $C_dictionaries_ID -o "..\parenttext-version-2\flows\parenttext_delivery_act.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_delivery_act"

#modules
python main.py create_flows $T_content_ID $C_modules_teen_ID -o "..\parenttext-version-2\flows\parenttext_modules.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_modules"
$crowdin_file_name = "modules_teen"  
#menu
python main.py create_flows  $T_C_menu_ID 
-o "..\parenttext-version-2\flows\parenttext_menu.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models  
$source_file_name = "parenttext_menu"

#goal checkin
python main.py create_flows $T_content_ID $C_goal_checkin_ID -o "..\parenttext-version-2\flows\parenttext_goalcheckin.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_goalcheckin"
$crowdin_file_name = "goal_checkins"

#dev assess
python main.py create_flows $T_content_ID $C_dev_asess_tool_ID -o "..\parenttext-version-2\flows\parenttext_dev_assess_tools.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_dev_assess_tools"
$crowdin_file_name = "dev_assess_tools"

#ltp activities
python main.py create_flows $T_content_ID $C_ltp_activities_ID -o "..\parenttext-version-2\parenttext_ltp_act_teen.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_ltp_act_teen"
$crowdin_file_name = "ltp_activities_teen
"
#malaysia demo
 python main.py create_flows $T_content_ID $C_malaysia_demo_ID -o "..\parenttext-version-2\flows\parenttext_malaysia.json" --format=google_sheets --datamodels=tests.input.parenttext.parenttext_models
$source_file_name = "parenttext_malaysia"

#>

Set-Location "..\parenttext-version-2"
Write-Output "created flows"
# localisation in flow creation?? 


################################
#step 1: edit flow properties (expiration, ...)
################################

################################
# step 2: flow edits (for all deployments) and localisation (changes specific to a deployment)
################################
 
  # "parenttext_onboarding" "parenttext_modules" "parenttext_goalcheckin" "parenttext_ltp_act_teen"
$flows =   $source_file_name +".json"
$SPREADSHEET_ID_ab = '1i_oqiJYkeoMsYdeFOcKlvvjnNCEdQnZlsm17fgNvK0s'
$JSON_FILENAME = "..\parenttext-version-2\flows\" + $flows
$source_file_name = $source_file_name + "_ABtesting"
#$output_path_2 = "parenttext-version-2\temp\" + $source_file_name + ".json"
$output_path_2 = "parenttext-" + $deployment + "-repo\temp\" + $source_file_name + ".json"
$AB_log = "..\parenttext-version-2\temp\AB_warnings.log"
Set-Location "..\rapidpro_abtesting"
python main.py $JSON_FILENAME ("..\parenttext-version-2\"  +$output_path_2) $SPREADSHEET_ID_ab --format google_sheets --logfile $AB_log 
Write-Output "added A/B tests and localisation"



Set-Location "..\parenttext-version-2"
# fix issues with _ui ?????not working?????
node ..\idems-chatbot-repo\fix_ui.js $output_path_2 $output_path_2
Write-Output "Fixed _ui"

################################
# step 3: add translation 
################################
$languages =  $languages
$2languages = $2languages
$deployment_ = $deployment_
$transl_output_folder = ".\parenttext-" + $deployment + "-repo\temp"

$input_path_T = $output_path_2
for ($i=0; $i -lt $languages.length; $i++) {
	$lang = $languages[$i]
    $2lang = $2languages[$i]

    #step T: get PO files from translation repo and merge them into a single json
    $transl_repo = "..\PLH-Digital-Content\translations\parent_text_v2\" + $2lang+ "\"
    $intern_transl = $transl_repo +  $2lang + "_" + $crowdin_file_name +".po"
    #$local_transl = $transl_repo +  $2lang+ "_" + $deployment_ + "_additional_messages.po"

    $json_intern_transl = ".\parenttext-"+ $deployment +"-repo\temp\temp_transl\"+ $lang+ "\"  +$2lang + "_" + $crowdin_file_name + ".json"
    node ..\idems_translation\common_tools\index.js convert $intern_transl $json_intern_transl

    #$json_local_transl = ".\parenttext-"+ $deployment +"-repo\temp\temp_transl\"+ $lang+ "\" +$2lang+ "_" + $deployment +"_additional_messages.json"
    #node ..\idems_translation\common_tools\index.js convert $local_transl $json_local_transl

    $json_translation_file_path = $json_intern_transl
    #$json_translation_file_path = ".\parenttext-"+ $deployment +"-repo\temp\temp_transl\"+ $lang+ "\" + $2lang+ "_all_messages.json"
    #node ..\idems_translation\common_tools\concatenate_json_files.js $json_local_transl $json_intern_transl $json_translation_file_path 


    $source_file_name = $source_file_name + "_" + $lang
    
    node ..\idems_translation\chatbot\index.js localize $input_path_T $json_translation_file_path $lang $source_file_name $transl_output_folder
   
    $input_path_T = $transl_output_folder + "\" + $source_file_name +".json"
    Write-Output ("Created localization for " + $lang)
}

################################
# step 4: text & translation edits for dictionaries
################################

################################
# step 5: integrity check 
################################

################################
# step 6: add quick replies to message text and translation
################################

################################
# step 7: safeguarding
################################

################################
# step 8. split files (if too big)?
################################










