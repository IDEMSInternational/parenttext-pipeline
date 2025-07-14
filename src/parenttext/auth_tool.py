import os
import json
import google.auth
from google.cloud import storage
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleAPIAuthenticator:
    """
    A class to handle flexible and automated authentication for Google Cloud APIs.

    It automatically determines the best authentication method in the following order:
    1. Service Account Key File (if key_path is provided and valid)
    2. Existing Authorized User Token (if token_file exists)
    3. OAuth 2.0 Client Secrets Flow (if credentials_file exists)
    4. Google Cloud Application Default Credentials (as a final fallback)
    """

    def __init__(
        self,
        scopes: list[str],
        key_path: str | None = None,
        credentials_file: str | None = None,
        token_file: str | None = None,
        project_id: str | None = None,
    ):
        """
        Initializes the authenticator.

        Args:
            scopes (list[str]): List of Google API scopes required.
            key_path (str | None): Path to the service account JSON key file.
            credentials_file (str | None): Path to the OAuth 2.0 client_secrets.json file.
            token_file (str | None): Path to the authorized user token.json file.
            project_id (str | None): Your Google Cloud project ID. If None, it will be inferred.
        """
        if not scopes:
            raise ValueError("The 'scopes' parameter cannot be empty.")
        self.scopes = scopes
        self.key_path = key_path
        self.credentials_file = credentials_file or "credentials.json"
        self.token_file = token_file or "token.json"
        self.project_id = project_id
        self.creds = None

    def authenticate(self):
        """
        Authenticates using the best available method. This method is called
        automatically by the service/client getters.

        Raises:
            Exception: If authentication fails through all available methods.
        """
        # If already authenticated and credentials are valid, do nothing.
        if self.creds and self.creds.valid:
            return

        # 1. Try Service Account Key File
        if self.key_path and os.path.exists(self.key_path):
            print(f"Attempting authentication using service account: {self.key_path}")
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    self.key_path, scopes=self.scopes
                )
                if not self.project_id:
                    with open(self.key_path, "r") as f:
                        self.project_id = json.load(f).get("project_id")
                print("Successfully authenticated using service account.")
            except Exception as e:
                print(f"Error authenticating with service account file: {e}")
                raise

        # 2. Try Existing Authorized User Token
        elif os.path.exists(self.token_file):
            print(f"Attempting authentication using token file: {self.token_file}")
            try:
                self.creds = Credentials.from_authorized_user_file(
                    self.token_file, self.scopes
                )
                if self.creds.expired and self.creds.refresh_token:
                    print("Credentials expired. Refreshing token...")
                    self.creds.refresh(Request())
                print("Successfully authenticated using authorized user file.")
            except Exception as e:
                print(f"Could not use token file ({e}). Will try other methods.")
                self.creds = None  # Ensure creds is None if refresh fails

        # 3. Try OAuth 2.0 Client Secrets Flow (Interactive)
        if not self.creds or not self.creds.valid:
            if os.path.exists(self.credentials_file):
                print(
                    f"Attempting authentication using client secrets file: {self.credentials_file}"
                )
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    self.creds = flow.run_local_server(port=0)
                    with open(self.token_file, "w") as token:
                        token.write(self.creds.to_json())
                    print(
                        f"Successfully authenticated and saved token to '{self.token_file}'."
                    )
                except Exception as e:
                    print(f"Error during OAuth 2.0 flow: {e}")
                    raise

        # 4. Fallback to Application Default Credentials
        if not self.creds:
            print(
                "No specific credentials provided or valid. Falling back to Application Default Credentials."
            )
            try:
                self.creds, self.project_id = google.auth.default(scopes=self.scopes)
                print(
                    "Successfully authenticated using Application Default Credentials."
                )
            except google.auth.exceptions.DefaultCredentialsError:
                print("Authentication failed. Could not find valid credentials.")
                raise Exception("Unable to authenticate.")

        # --- Finalize project ID ---
        if not self.project_id and hasattr(self.creds, "project_id"):
            self.project_id = self.creds.project_id

    def get_storage_client(self) -> storage.Client:
        """Authenticates and returns a Google Cloud Storage client."""
        self.authenticate()
        if not self.project_id:
            print(
                "Warning: Project ID could not be determined. You may need to specify it manually for GCS."
            )
        return storage.Client(project=self.project_id, credentials=self.creds)

    def get_sheets_service(self, version="v4"):
        """Authenticates and returns a Google Sheets service object."""
        self.authenticate()
        return build("sheets", version, credentials=self.creds)

    def get_drive_service(self, version="v3"):
        """Authenticates and returns a Google Drive service object."""
        self.authenticate()
        return build("drive", version, credentials=self.creds)


if __name__ == "__main__":
    # --- Example Usage ---
    # Replace with your actual project ID and file paths.

    MY_PROJECT_ID = "your-gcp-project-id"  # <-- REPLACE
    SERVICE_ACCOUNT_FILE = "service-account-key.json"  # <-- REPLACE
    CLIENT_SECRETS_FILE = "client_secrets.json"  # <-- REPLACE
    TOKEN_FILE = "token.json"  # Custom token file name

    # --- Example 1: Google Cloud Storage ---
    print("--- Testing Google Cloud Storage ---")
    try:
        gcs_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        auth_gcs = GoogleAPIAuthenticator(
            scopes=gcs_scopes, key_path=SERVICE_ACCOUNT_FILE, project_id=MY_PROJECT_ID
        )
        gcs_client = auth_gcs.get_storage_client()

        print("\n--- Listing GCS Buckets ---")
        buckets = gcs_client.list_buckets()
        for bucket in buckets:
            print(f"- {bucket.name}")
        print("---------------------------\n")

    except Exception as e:
        print(f"GCS test failed: {e}")

    # --- Example 2: Google Drive ---
    print("\n--- Testing Google Drive API ---")
    try:
        # Note: For user-centric APIs like Drive/Sheets, using client_secrets is more common.
        # A service account would need to be granted domain-wide delegation.
        drive_scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        auth_drive = GoogleAPIAuthenticator(
            scopes=drive_scopes,
            credentials_file=CLIENT_SECRETS_FILE,
            token_file=TOKEN_FILE,
        )
        drive_service = auth_drive.get_drive_service()

        print("\n--- Listing 10 Files from Google Drive ---")
        results = (
            drive_service.files()
            .list(pageSize=10, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
        else:
            for item in items:
                print(f"- {item['name']} ({item['id']})")
        print("----------------------------------------\n")

    except Exception as e:
        print(f"Drive test failed: {e}")

    # --- Example 3: Google Sheets ---
    print("\n--- Testing Google Sheets API ---")
    try:
        # Using the same authenticator as Drive since the token will have the necessary scope
        # If you needed different scopes, you would create a new authenticator instance.
        sheets_scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        auth_sheets = GoogleAPIAuthenticator(
            scopes=sheets_scopes,
            credentials_file=CLIENT_SECRETS_FILE,
            token_file="sheets_token.json",  # Use a different token file for different scopes
        )
        sheets_service = auth_sheets.get_sheets_service()

        # Use a public spreadsheet for this example
        spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        spreadsheet_range = "Class Data!A2:E"

        print("\n--- Reading data from public spreadsheet ---")
        sheet = sheets_service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=spreadsheet_range)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
        else:
            print("Name, Gender:")
            for row in values[:5]:  # Print first 5 rows
                print(f"- {row[0]}, {row[1]}")
        print("-------------------------------------------\n")

    except Exception as e:
        print(f"Sheets test failed: {e}")
