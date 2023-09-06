import json
import os
import time

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
import csv

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def google_sheets_as_csv(sheet_ids, output_folder):

    service = build('sheets', 'v4', credentials=get_credentials())
    for sheet_id in sheet_ids:
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = spreadsheet['sheets']
        workbook_name = spreadsheet['properties']['title']
        workbook_folder = os.path.join(output_folder, workbook_name)
        os.makedirs(workbook_folder, exist_ok=True)

        for sheet in sheets:
            sheet_title = sheet['properties']['title']
            range_name = f"'{sheet_title}'"

            request = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name)
            response = None

            while response is None:
                try:
                    response = request.execute()
                except Exception as e:
                    if 'quota' in str(e).lower():
                        print("Rate limit exceeded. Backing off and retrying...")
                        time.sleep(10)  
                    else:
                        raise

            csv_path = os.path.join(workbook_folder, f"{sheet_title}.csv")

            with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:  # Specify encoding
                csv_writer = csv.writer(csv_file)
                csv_writer.writerows(response['values'])

        print(f"Workbook '{workbook_name}' processed and downloaded to csv")


def get_credentials():
    sa_creds = os.getenv("CREDENTIALS")
    if sa_creds:
        return ServiceAccountCredentials.from_service_account_info(
            json.loads(sa_creds),
            scopes=SCOPES
        )
    
    creds = None
    token_file_name = "token.json"

    if os.path.exists(token_file_name):
        creds = Credentials.from_authorized_user_file(
            token_file_name,
            scopes=SCOPES
        )

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_file_name, 'w') as token:
            token.write(creds.to_json())

    return creds


