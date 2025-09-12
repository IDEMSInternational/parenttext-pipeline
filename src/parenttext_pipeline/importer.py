import abc
from argparse import ArgumentParser
from playwright.sync_api import sync_playwright, Page, Error, Browser, expect
import time

class ImporterError(Exception):
    pass

class Importer(abc.ABC):
    """Abstract Base Class defining the importer interface."""
    def __init__(self, page: Page, host: str):
        self.page = page
        self.host = host

    @abc.abstractmethod
    def login(self, username, password):
        raise NotImplementedError

    @abc.abstractmethod
    def select_workspace(self, workspace_name):
        raise NotImplementedError

    def upload(self, definition_fp):
        print(f"Uploading file: {definition_fp}...")
        
        self.page.goto(self.upload_url)
        self.page.locator('input[type="file"]').set_input_files(definition_fp)

        submit_button = self.page.locator('button[type="submit"], input[type="submit"]')
        if submit_button.count() > 0:
            submit_button.first.click()
            self.page.wait_for_load_state('networkidle')

        wait_and_see = [
            "In progress",
            "About to start",
        ]
        
        if any(text in self.page.content() for text in wait_and_see):
            print("In progress", end="")
            counter = 0
            while any(text in self.page.content() for text in wait_and_see):
                time.sleep(1)
                print(".", end="")
                counter += 1
                if counter > 300:
                    print("Timeout ")
                    break
            print(" Done")
        
        if self.upload_success_msg not in self.page.content():
            raise ImporterError("Import failed, content did not confirm success. See screenshot.")
        print(f"Import of {definition_fp} completed successfully.")

    @abc.abstractmethod
    def logout(self):
        raise NotImplementedError

class TextItImporter(Importer):
    """Importer for the TextIt server environment."""
    def __init__(self, page: Page, host: str):
        super().__init__(page, host)
        self.upload_url = f"{self.host}/orgimport/create/"
        self.upload_success_msg = "Finished successfully"

    def login(self, username, password):
        print("Attempting TextIt login...")
        url = f"{self.host}/accounts/login/?next=/msg/"
        self.page.goto(url)
        self.page.locator('input[name="login"]').fill(username)
        self.page.locator('input[name="password"]').fill(password)
        self.page.locator('button[type="submit"]').click()
        try:
            self.page.wait_for_url(f"{self.host}/msg/", timeout=10000)
            print(f"Login completed, url={self.page.url}, username={username}")
        except Error:
            raise ImporterError("Login failed. Was not redirected to inbox.")

    def select_workspace(self, workspace_name):
        print(f"Switching to workspace {workspace_name}...")
        self.page.locator("#dd-workspace").click()
        try:
            expect(self.page.get_by_text(workspace_name, exact=True, )).to_be_visible(timeout=0.5)
            print(f"Already in workspace {workspace_name}")
            return
        except:
            pass
        try:
            self.page.locator("#dd-workspace > div:nth-child(2) > temba-workspace-select").click()
        except:
            expect(self.page.get_by_text(workspace_name, exact=True, )).to_be_visible(timeout=3)
            print(f"Already in workspace {workspace_name}")
            return
        try:
            self.page.get_by_text(workspace_name, exact=True).click()
        except Error:
            raise ImporterError(f"Workspace name '{workspace_name}' does not exist.")
        print(f"Switched to workspace {workspace_name}")

    def logout(self):
        print("Logging out...")
        url = f"{self.host}/accounts/logout/"
        self.page.goto(url)
        self.page.locator('button[type="submit"]').click()
        try:
            # Wait for redirection to the login or home page
            self.page.wait_for_url(f"{self.host}/", timeout=10000)
            print("Logout completed.")
        except Error:
            raise ImporterError("Logout failed. Did not redirect correctly.")

class InternalImporter(Importer):
    """
    Importer for the internal test server environment.
    """
    def __init__(self, page: Page, host: str):
        super().__init__(page, host)
        self.upload_url = f"{self.host}/org/import/"
        self.upload_success_msg = "Import successful"

    def login(self, username, password):
        print("Attempting Internal Server login...")

        url = f"{self.host}/users/login/"
        self.page.goto(url)
        self.page.locator('input[name="username"]').fill(username)
        self.page.locator('input[name="password"]').fill(password)
        self.page.locator('input[type="submit"]').click()
        try:
            self.page.wait_for_url(f"{self.host}/org/choose/", timeout=10000)
            print(f"Login completed, url={self.page.url}, username={username}")
        except Error:
            raise ImporterError("Login failed. Was not redirected to expected page.")

    def select_workspace(self, workspace_name):
        try:
            self.page.get_by_text(workspace_name, exact=True).click()
        except Error:
            raise ImporterError(f"Workspace name '{workspace_name}' does not exist.")

    def logout(self):
        print("Logging out...")
        url = f"{self.host}/users/logout/"
        self.page.goto(url)
        try:
            self.page.wait_for_url(f"{self.host}/users/login/", timeout=10000)
            print("Logout completed.")
        except Error:
            raise ImporterError("Logout failed. Did not redirect correctly.")


def get_importer(importer_type: str, page: Page, host: str) -> Importer:
    """Factory function to get the correct importer instance."""
    if importer_type == "textit":
        return TextItImporter(page, host)
    elif importer_type == "internal":
        return InternalImporter(page, host)
    else:
        raise ValueError(f"Unknown importer type: {importer_type}")

danger_words = ["API", "token"]

def print_error(e: Exception, page: Page):
    """Prints detailed error information, including a screenshot."""
    print("\n" + "#" * 30)
    print("## PAGE CONTENT (truncated)")
    try:
        text_content = page.locator('body').inner_text(timeout=500)
        if any([danger in text_content for danger in danger_words]):
            print("### FATAL ERROR ###")
            print(f"An exception occurred: {e}")
            print("contained potentially sensitive information, so full html/screenshot not output")
            return

        print(text_content[:1000])
    except Error:
        print(page.content()[:1000])
    print("#" * 30)
    print("### FATAL ERROR ###")
    print(f"An exception occurred: {e}")
    screenshot_path = "import_failure.png"
    page.screenshot(path=screenshot_path)
    print(f"A screenshot has been saved to: {screenshot_path}")
    print(f"## Final URL: {page.url}")
    print("#" * 30)

def main_import_flow(importer_type, host, username, password, deployment, definitions):
    """Main execution flow."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        error_occured = False
        try:
            importer = get_importer(importer_type, page, host)
            importer.login(username, password)
            importer.select_workspace(deployment)
            for fp in definitions:
                importer.upload(fp)
            importer.logout()
            print("\nAll definitions imported successfully!")
            print(f"## Final URL: {page.url}")
        except (ImporterError, Error) as e:
            print_error(e, page)
            error_occured = True
        finally:
            browser.close()
        if error_occured:
            exit(1)

def cli():
    parser = ArgumentParser(description="Import a flow definition into a RapidPro server")
    parser.add_argument(
        "-t",
        "--type",
        required=True,
        choices=["textit", "internal"],
        help="The type of server to connect to.",
    )
    parser.add_argument("-H", "--host", required=True, help="URL of the server")
    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-d", "--deployment", required=True, help="The workspace name")
    parser.add_argument("definition_files", nargs="+", help="File(s) with flow definitions")
    args = parser.parse_args()
    main_import_flow(
        args.type,
        args.host,
        args.username,
        args.password,
        args.deployment,
        args.definition_files,
    )

if __name__ == "__main__":
    cli()
