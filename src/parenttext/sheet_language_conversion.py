import json
import re
import difflib

import os
from rpft.google import get_credentials
from googleapiclient.discovery import build


# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json' # Your OAuth 2.0 Client ID JSON
TOKEN_FILE = 'token.json' # File to store the user's token after first authorization

# dictionary with keys as spreadsheet IDs and values as lists of range names to apply function to
# Intended use: Find the ranges for a given spreadsheet type (e.g. LTP activities) and locally change the ID
# or add new ranges for file type and commit
spreadsheet_ranges = {
    # '17JvNuwr3yzX2ErwSnV0I4WUU2ERc32lxqGHVudrDhyA': [ # Testing MX Modules - All ages
    #     'Being a More Responsible and Involved Caregiver!C2:ZZ'
    # ],
    # '1YTkeeZvnI2Uil6cirBCaEcRAfqsZHnplBwIA64tNJH4': [ # Testing MX Modules - Child
    #     'Improve My Relationship with My Child!C2:ZZ',
    #     'Keep My Girl or Boy Safe and Healthy!C2:ZZ',
    #     'Manage My Girl or Boy Behaviour!C2:ZZ',
    #     'Prepare My Child for Success in School!C2:ZZ',
    #     'Understand My Girl or Boy Development!C2:ZZ'
    # ],
    # '1ys3ctng5sJLnFMQ8M6TWVEk2RQFL-xe_PzR8z73RC6A': [ # Testing MX Modules - Teen
    #     'Improve My Relationship with My Teen!C2:ZZ',
    #     'Teen Health and Safety!C2:ZZ',
    #     'Support My Teen’s Education!C2:ZZ',
    #     'Manage My Teen’s Behaviour!C2:ZZ',
    #     'Understanding My Teen!C2:ZZ'
    # ],
    # '1-0Kj3N2F6MU15Vl53vDF8HT0TQWWTHQ5GSm8XqYGonU': [ # Testing MX LTP activities
    #     'ltp_activity_teen_data!B2:C',
    #     'ltp_activity_child_data!B2:C',
    # ],
    # '1HERSo5By7fuOhLWQmrSIrT89fWcR8T-AhEy48oqjkj0': [ # Testing MX Troubleshooting
    #     'goal_checkin_teen_data!B2:C',
    #     'goal_checkin_teen_data!E2:I',
    #     'goal_checkin_teen_data!K2:ZZ',
    #     'goal_checkin_all_ages_data!B2:C',
    #     'goal_checkin_all_ages_data!E2:I',
    #     'goal_checkin_all_ages_data!K2:ZZ',
    #     'goal_checkin_child_data!B2:C',
    #     'goal_checkin_child_data!E2:I',
    #     'goal_checkin_child_data!K2:ZZ',
    #     'survey_behave_teen_data!B2:ZZ',
    #     'survey_behave_child_data!B2:ZZ'
    # ],
    '1qwL_l1RJsuuJHGz16J6u63jdLESoc7P0o4Ka1aLhHGE': [ # Delivery Data
        'congrats_data!B2:C',
        'delivery_messages!B2:D',
        'make_options_wrapper_data!E2:M',
        'show_options_wrapper_data!E2:G',
        'description_data!B2:C',
        'interaction_data!E2:E',
        'interaction_data!H2:H',
        'interaction_data!J2:J',
        'activity_offer_data!C2:L',
        'activity_offer_data!N2:N',
        'activity_type_data!B2:C',
        'pre_post_goal_checkin_messages!B2:B',
        'certificate_name_data!C2:C',
        'certificate_name_data!I2:I',
        'certificate_name_data!M2:O',
    ],
    '1uhv_AKkGz6fn6JjTCSt5vUKQBpc46mzG8n98zkAsd9c': [ # menu data
        'menu_data!B2:B',
        'menu_data!D2:D',
        'menu_data!F2:F',
        'menu_data!H2:H',
        'menu_data!J2:J',
        'menu_data!L2:L',
        'menu_data!N2:N',
        'menu_data!P2:P',
        'menu_data!R2:R',
        'menu_blocks_data!B2:D',
        'menu_blocks_data!F2:F',
        'menu_blocks_data!H2:H',
        'menu_blocks_data!J2:J',
        'menu_blocks_data!L2:L',
        'menu_blocks_data!N2:N',
        'menu_blocks_data!P2:P',
        'review_skills_menu_data!B2:B',
        'troubleshooting_menu_data!B2:B',
        'menu_progress_main_data!B2:C',
        'menu_messages!B2:D',
        'settings_profile_data!B2:F',
        'settings_profile_data!I2:I',
        'settings_profile_data!K2:K',
        'settings_profile_data!M2:M',
        'settings_profile_data!O2:O',
        'settings_profile_data!Q2:Q',
        'settings_profile_data!S2:S',
        'settings_profile_data!U2:U',
        'make_options_wrapper_menu_data!E2:M',
        'settings_certificate_data!B2:F',
    ],
    '11oSH7YbRXpXSvEK4dWntZPF-r2RF7MsbYsToRHFHcW8': [ # onboarding data
        'onboarding_messages!B2:C',
        'onboarding_survey!C2:C',
        'onboarding_survey!H2:H',
        'onboarding_survey!K2:K',
        'onboarding_survey!N2:N',
        'onboarding_survey!Q2:Q',
        'onboarding_survey!T2:T',
        'onboarding_survey!W2:W',
        'onboarding_survey!Z2:Z',
        'onboarding_survey!AC2:AC',
        'onboarding_survey!AS2:AS',
        'onboarding_survey!AX2:AX',
        'onboarding_survey!BC2:BC',
        'survey_defaults!B2:B',
    ],
    '1I9UnAGc9eA7k-9miJty0kyj0mYYuVEz-4Q99ll4-qk0': [ # safeguarding data
        'safeguarding_leave_programme_data!B2:C',
        'safeguarding_start_programme_data!B2:C',
        'referrals!B2:C',
        'safeguarding_entry_data!B2:C',
        'safeguarding_entry_data!E2:E',
        'safeguarding_entry_data!G2:H',
        'safeguarding_trigger_wrapper_data!B2:G',
        'id_generator_data!B2:B',
        'safeguarding_wfr_interaction_data!B2:B',
        'safeguarding_help_data!B2:B',
        'uncaught_message_flow_data!B2:B',
        'book_trigger_data!B2:B',
    ]
        
}
file_prefix = 'Translated'

file_path = 'merged_translations.json' # Define the path to your JSON translations file

# Snippets in the translations that must be backconverted to the format of the sheets
translation_substitutions = {
    "SourceText": {
        "your {teen}": "Your Teen",
        "your {child}": "Your Child",
        "Your {teen}": "Your Teen",
        "Your {child}": "Your Child",
    },
    "text": {
        "tu {teen}": "{tu adolescente}",
        "tu {child}": "{tu niño}",
        "Tu {teen}": "{Tu adolescente}",
        "Tu {child}": "{Tu niño}",
    }
}

placeholder_substitutions_without_brackets = {
    "F1_MOTHER": "F1_MADRE",
    "F1_FATHER": "F1_PADRE",
    "F1_SON_17": "F1_HIJO_17",
    "F1_DAUGHTER_16": "F1_HIJA_16",
    "F1_DAUGHTER_13": "F1_HIJA_13",
    "F1_DAUGHTER_6": "F1_HIJA_6",
    "F1_DAUGHTER_2": "F1_HIJA_2",
    "F1_SON_5": "F1_HIJO_5",
    "F2_GRANDMOTHER": "F2_ABUELA",
    "F2_GRANDFATHER": "F2_ABUELO",
    "F2_DAUGHTER_17": "F2_HIJA_17",
    "F2_SON_15": "F2_HIJO_15",
    "F2_SON_8": "F2_HIJO_8",
    "F2_DAUGHTER_3": "F2_HIJA_3",
    "F3_MOTHER": "F3_MADRE",
    "F3_UNCLE": "F3_TÍO",
    "F3_DAUGHTER_12": "F3_HIJA_12",
    "F3_DAUGHTER_7": "F3_HIJA_7",
    "F3_SON_4": "F3_HIJO_4",
    "FRIEND_FEMALE_1": "AMIGA_MUJER_1",
    "FRIEND_FEMALE_2": "AMIGA_MUJER_2",
    "MAN_IN_CAR": "HOMBRE_EN_COCHE",
    "BOYFRIEND": "NOVIO",
    "MAN_THREAT": "HOMBRE_AMENAZANTE",
    "GIRLFRIEND": "NOVIA",
    "TEACHER_1": "PROFESOR_1",
}

placeholder_substitutions = {"{"+key+"}": "{"+value+"}" for key, value in placeholder_substitutions_without_brackets.items()}
translation_substitutions["text"].update(placeholder_substitutions) # Add the placeholder substitutions to the text substitutions   

# Patterns like WhatsApp Tailoring to be removed at time of translation attempt, capture group the stuff to keep
tailoring_patterns = [
    r'^\*([^\*].*[^\*])\*$', # Bolding, but not **_**
    r'^\d+\. (.*)$', # Option Numbers in surveys
]

# Message Splitting on new lines
# Must be wrapped in capture group () to keep delimiters
# TODO: replace with the same logic actually used for splitting, rather than recoding
# message_splitting = r'\n\s*[\n;]+' # Lots of single \n missed
message_splitting = r'([\r\n;|]\s*)' # some messages shouldn't be split on \r
# message_splitting = r'([\n;|]\s*)' # some messages need to be split on \r


## --- Substitution Setup ---
# Open the JSON file in read mode ('r')
with open(file_path, 'r', encoding='utf-8') as file:
    # Use json.load() to parse the JSON data and load it into a Python object
    merged_translations = json.load(file)

# Messages to find and replace in the sheet cells
message_replacements = {}

for translation in merged_translations:
    out_translation = {}
    # Iterate over the components of each translation entry
    for key in translation_substitutions.keys():
        s = translation[key].rstrip().lstrip() # Trim whitespace, as some occurs in the translation file
        # Iterate over each substitution 
        for pat,repl in translation_substitutions[key].items():
            s = re.sub(pat, repl, s)

        out_translation[key] = s

    message_replacements[out_translation["SourceText"]] = out_translation["text"]

## --- Tailoring Removal ---

def check_tailoring(m):
    try:
        most_similar_SourceText = difflib.get_close_matches(m, message_replacements.keys(), n=1, cutoff=0.8)[0]
    except IndexError: # No close matches, just return none
        return None

    most_similar_text = message_replacements[most_similar_SourceText]
    for pattern in tailoring_patterns:
        if re.search(pattern, most_similar_SourceText) and re.search(pattern, most_similar_text):
            return re.sub(pattern, r'\1', most_similar_text)
            


## --- Message Replacement ---
try:
    with open("language_conversion_errors.json", "r") as f:
        untranslated_message_locations = json.load(f)
except FileNotFoundError:
    untranslated_message_locations = {}

def replace_messages(cell_value, cell_loc):
    if cell_value == '': # Don't try to replace empty cells
        return cell_value
    out_messages = []
    # Break into messages 
    messages = re.split(message_splitting, cell_value)
    failures = False
    for m in messages:
        if re.search(message_splitting, m): # Skip delimiters
            out_messages.append(m)
            continue
        m = m.rstrip().lstrip()

        # If m is directly in message replacements, append and continue
        if m in message_replacements.keys():
            out_messages.append(message_replacements[m])
            continue
        
        tailored_output = check_tailoring(m)
        if tailored_output is not None:
            out_messages.append(tailored_output)
            continue
        
        # if output cant be tailored, it fails
        failures = True
        # If any message in the cell has already been translated, don't attempt to translate other cells
        if m in message_replacements.values():
            # print('cell {cell_loc} already translated')
            # Break to not record cell in untranslated message log
            break
        # print(f'No replacement found for cell {cell_loc} message "{m}"')
        
        
        # Record the cell locations of untranslated messages
        if m in untranslated_message_locations.keys():
            untranslated_message_locations[m]['locations'].append(cell_loc)
        else:
            most_similar_messages = difflib.get_close_matches(m, message_replacements.keys(), n=3, cutoff=0.6)
            most_similar = {message: message_replacements[message] for message in most_similar_messages}
            untranslated_message_locations[m] = {
                'most similar': most_similar,
                'locations': [cell_loc]
            }
    
    if failures: # If any messages fail to translate, return original cell value
        return cell_value
    return ''.join(out_messages) # Join and return the output messages


## -- Google Auth --
def get_service(service_name, service_version):
    """Authenticates using OAuth 2.0 Client ID and returns a Google Sheets service object."""
    creds = get_credentials()    
    service = build(service_name, service_version, credentials=creds)
    return service

def get_sheets_service():
    return get_service('sheets', 'v4')

def get_drive_service():
    return get_service('drive', 'v3')

## -- Cell Location Helper --
def get_excel_column_letter(col_index):
    """
    Converts a 0-indexed column number to its Excel-style column letter.
    (0 -> A, 1 -> B, ..., 25 -> Z, 26 -> AA, etc.)
    """
    result = ""
    while col_index >= 0:
        remainder = col_index % 26
        result = chr(65 + remainder) + result
        col_index = (col_index // 26) - 1
    return result

def cell_location(range_name, sheet_name, col_index, row_index):
    """
    Calculates the cell location based on a range name, column index, and row index.

    Args:
        range_name (str): The Excel range name (e.g., "Sheet1!A1:B10").
        col_index (int): The 0-based column offset from the starting column.
        row_index (int): The 0-based row offset from the starting row.

    Returns:
        str: The calculated cell location (e.g., "Sheet1!B5").
    """
    sheet, cells = range_name.split('!')
    cell_start, _ = cells.split(':') # get the starting cell
    
    # Extract the starting column letters and row number
    start_col_letters = "".join(re.findall(r'[A-Za-z]+', cell_start))
    start_row_number = int("".join(re.findall(r'\d+', cell_start)))

    # Convert starting column letters to a 0-indexed number
    current_col_num = 0
    for char in start_col_letters.upper():
        current_col_num = current_col_num * 26 + (ord(char) - ord('A') + 1)
    # Adjust to be 0-indexed
    current_col_num -= 1 

    # Calculate the new column index
    new_col_index = current_col_num + col_index

    # Convert the new column index back to Excel-style letters
    new_col_letters = get_excel_column_letter(new_col_index)
    
    # Calculate the new row number
    new_row_number = start_row_number + row_index
    
    return f'[{sheet_name}] {sheet}!{new_col_letters}{new_row_number}'


## --- Copy File ---
def copy_file(spreadsheet_id, new_file_title):
    service = get_drive_service()
    copied_file = service.files().copy(
        supportsAllDrives=True, # needed for shared folders
        fileId=spreadsheet_id,
        body={
            'name': new_file_title
        },
        fields="id, webViewLink"  # Specify the fields you want in the response (e.g., id and webViewLink)
    ).execute()
    print(f'Copied to {new_file_title}: {copied_file['webViewLink']}')
    return copied_file['id']


## -- Sheets API Function-Apply --

def sheets_apply(spreadsheet_id, range_name, function, dry_run=False):
    """Reads data from a spreadsheet, applies a function, and writes it back.

    Parameters
    ----------
    spreadsheet_id : str
        ID of the spreadsheet to access
    range_name : str
        The range to apply the function to, e.x. 'Sheet1!C2:Z'
    function : function
        A function that takes cell_value and cell_loc as arguments and returns a value to be written to the sheet
    """
    # Authenticate
    service = get_sheets_service()

    # --- Get Title ---
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    # Extract the title from the metadata
    spreadsheet_title = sheet_metadata.get('properties', {}).get('title', 'Untitled Spreadsheet')

    # --- Read Data ---
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])


    if not values:
        print('No data found in the specified range.')
        return

    # --- Apply Function and Prepare for Batch Update ---
    updated_values = []
    for row_index, row in enumerate(values):
        new_row = []
        for col_index, cell_value in enumerate(row):
            transformed_value = function(cell_value, cell_location(range_name, spreadsheet_title, col_index, row_index))
            new_row.append(transformed_value)
        updated_values.append(new_row)

    # --- Batch Update Data ---
    body = {
        'values': updated_values
    }
    
    # Use spreadsheets().values().update() for simple value updates
    # This will overwrite the existing range with the new data
    if not dry_run:
        update_result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',  # 'RAW' for literal values, 'USER_ENTERED' for formulas/rich text
            body=body
        ).execute()

        print(f"{update_result.get('updatedCells')} cells updated.")
        print(f"Update Range: {update_result.get('updatedRange')}")
    else:
        print(f"Dry run range: {range_name}")


## --- main ---

def main(spreadsheet_ranges, as_copy = True, dry_run = False):
    for spreadsheet_id, range_list in spreadsheet_ranges.items():
        # --- make copy ---
        if as_copy:
            service = get_sheets_service()
            # Get spreadsheet metadata
            sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            # Extract the title from the metadata
            spreadsheet_title = sheet_metadata.get('properties', {}).get('title', 'Untitled Spreadsheet')
            new_file_title = ' '.join([file_prefix, spreadsheet_title])
            spreadsheet_id = copy_file(spreadsheet_id, new_file_title)

        for range_name in range_list:
            print(f"\nWorking on {range_name} in spreadsheet {spreadsheet_id}")
            sheets_apply(spreadsheet_id, range_name, replace_messages, dry_run)

if __name__ == "__main__":
    main(spreadsheet_ranges, as_copy=False, dry_run=True) # Dry Run
    # main(spreadsheet_ranges, as_copy=True, dry_run=False) # Hot Run
    with open("language_conversion_errors.json", "w") as f:
        json.dump(untranslated_message_locations, f, indent=4) # indent for pretty-printing
    print(f'Total untranslated messages: {len(untranslated_message_locations.keys())}')