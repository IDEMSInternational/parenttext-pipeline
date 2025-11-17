"""
# media_ops.py
This script orchestrates the media processing pipeline, including downloading assets from Canto,
transcoding them, and uploading to Google Cloud Storage.
It integrates with the Firebase tools for managing media versions in the cloud.
It is designed to be run as a standalone script, with command-line arguments for configuration.
For help, run:
    python -m parenttext.media_ops --help
"""

import argparse
import shutil
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from os import getenv

from requests import ConnectionError

from parenttext.canto import main as canto_main
from parenttext.transcode import transcode_dir
from parenttext.firebase_tools import Firebase

from parenttext.referenced_assets import get_referenced_assets, get_parenttext_paths
from parenttext.placeholder_gen import create_placeholder_files

from parenttext.validate_assets import process_media_urls


env = {}


def safe_getenv(key, default):
    if key not in env.keys():
        env[key] = getenv(key)

    if env[key] is None:
        env[key] = default

    return env[key]


def step_canto_download(try_count = 0):    
    try:
        canto_main("canto")
    except ConnectionError as e:
        print(e)
        step_canto_download(try_count + 1)
    


def step_transcode():

    transcode_path = safe_getenv("MEDIA_OPS_TRANSCODE_FOLDER", "transcoded")
    old_structure = safe_getenv("MEDIA_OPS_OLD_STRUCTURE", False)

    transcode_dir(
        src=Path("canto"),
        dst=Path(transcode_path),
        env=env,
        old_structure=old_structure
    )

    env["MEDIA_OPS_UPLOAD_FOLDER"] = transcode_path


def step_firebase_versioned_upload():

    upload_folder = safe_getenv("MEDIA_OPS_UPLOAD_FOLDER", "transcoded")

    fb = Firebase(project_id=env["GCS_PROJECT_ID"])
    fb.upload_new_version(
        source_directory=upload_folder,
        bucket_name=env["GCS_BUCKET_NAME"],
        remote_directory=env["DEPLOYMENT_ASSET_LOCATION"],
        dry_run=env["dry_run"],
    )

    print(
        "Now to change the version in RapidPro flows the user must:\n"
        "Update variables: RapidPro -> flows -> @ Globals\n"
        "Push those updates to users: RapidPro -> flows -> update_attachment_path_version"
        " -> Start -> select group 'enrolled' -> click start button"
    )


def step_firebase_non_versioned_upload():

    upload_folder = safe_getenv("MEDIA_OPS_UPLOAD_FOLDER", "transcoded")

    fb = Firebase(project_id=env["GCS_PROJECT_ID"])
    fb.upload_folder(
        local_base_path=upload_folder,
        bucket_name=env["GCS_BUCKET_NAME"],
        gcs_base_path=env["DEPLOYMENT_ASSET_LOCATION"],
        dry_run=env["dry_run"],
    )


def get_referenced_asset_list(root):
    rapidpro_file = safe_getenv("RAPIDPRO_OUTPUT", "./output/parenttext_all.json")
    with open("config.json", "r") as fh:
        language_dict = json.load(fh)["sources"]["media_assets"]["mappings"]["Language"]
    language_list = list(language_dict.values())

    gender_list = ["male", "female"]  # Sexs will be replaced with genders soon...

    path_dict = get_parenttext_paths(root, language_list, gender_list)
    print(path_dict)

    asset_list = get_referenced_assets(rapidpro_file, path_dict)

    return asset_list


def get_root():
    rapidpro_file = safe_getenv("RAPIDPRO_OUTPUT", "./output/parenttext_all.json")
    with open(rapidpro_file, 'r', errors="ignore") as f:
        content = f.read()

    pattern = r'\s*"field": {\n\s*"key": "path",\n\s*"name": "path"\n\s*},'
    match = re.search(pattern, content, re.DOTALL)

    line = None
    if match:
        end_of_match_pos = match.end()
        next_newline_pos = content.find('\n', end_of_match_pos)

        if next_newline_pos != -1:
            start_of_next_line = next_newline_pos + 1
            end_of_next_line = content.find('\n', start_of_next_line)
            if end_of_next_line != -1:
                line = content[start_of_next_line:end_of_next_line].strip()
            else:
                line = content[start_of_next_line:].strip()
    
    if line:
        pattern = r'(?:"value": "@\(\\")([^\\"]*)'
        match = re.findall(pattern, line)
        return match[0]
    return None


def step_placeholder_gen():

    placeholder_directory = safe_getenv(
        "MEDIA_OPS_PLACEHOLDER_FOLDER", "placeholder_assets"
    )

    asset_list = get_referenced_asset_list(placeholder_directory)

    create_placeholder_files(asset_list)

    env["MEDIA_OPS_UPLOAD_FOLDER"] = placeholder_directory


def step_list_referenced_assets():
    print("#" * 30)
    asset_list = get_referenced_asset_list("canto")
    asset_list.sort()
    print(json.dumps(asset_list, indent=2))


def step_list_missing_assets():

    referenced = set(get_referenced_asset_list("canto"))
    downloaded = set([p.as_posix() for p in Path("canto").rglob("*") if p.is_file()])

    missing = list(referenced - downloaded)
    missing.sort()
    unreferenced = list(downloaded - referenced)
    unreferenced.sort()

    union = list(referenced.intersection(downloaded))
    union.sort()

    print("#" * 30)
    print(f"Correct assets: {len(union)}")
    print(json.dumps(union, indent=2))

    print("#" * 30)
    print(f"Missing assets: {len(missing)}")
    print(json.dumps(missing, indent=2))

    print("#" * 30)
    print(f"Unreferenced/Extra assets: {len(unreferenced)}")
    print(json.dumps(unreferenced, indent=2))


def step_verify_assets():
    root = "/".join([get_root().rstrip("/"), get_deployment()])
    asset_list = get_referenced_asset_list(root)
    asset_list.sort()
    process_media_urls(asset_list)


step_dict = {
    "canto_download": {
        "fn": step_canto_download,
        "start_msg": "Starting Canto download",
        "end_msg": "Canto download complete",
        "required_env": [
            "CANTO_APP_ID",
            "CANTO_APP_SECRET",
            "CANTO_USER_ID",
        ],
    },
    "transcode": {
        "fn": step_transcode,
        "start_msg": "Starting media transcoding",
        "end_msg": "Transcoding complete",
        "required_env": [ # needed to reduce transcode time and double uploads
            "DEPLOYMENT_ASSET_LOCATION",
            "GCS_PROJECT_ID",
            "GCS_BUCKET_NAME",
        ],
    },
    "firebase_versioned_upload": {
        "fn": step_firebase_versioned_upload,
        "start_msg": "Starting upload to Firebase Storage",
        "end_msg": "Firebase upload complete",
        "required_env": [
            "DEPLOYMENT_ASSET_LOCATION",
            "GCS_PROJECT_ID",
            "GCS_BUCKET_NAME",
        ],
    },
    "firebase_non_versioned_upload": {
        "fn": step_firebase_non_versioned_upload,
        "start_msg": "Starting upload to Firebase Storage",
        "end_msg": "Firebase upload complete",
        "required_env": [
            "DEPLOYMENT_ASSET_LOCATION",
            "GCS_PROJECT_ID",
            "GCS_BUCKET_NAME",
        ],
    },
    "placeholder_gen": {
        "fn": step_placeholder_gen,
        "start_msg": "Creating directory of placeholder assets",
        "end_msg": "Placeholders created",
    },
    "list_referenced_assets": {
        "fn": step_list_referenced_assets,
        "start_msg": "Printing list of assets referenced by flows",
        "end_msg": "List of assets printed",
    },
    "list_missing_assets": {
        "fn": step_list_missing_assets,
        "start_msg": "Printing list of missing assets and unreferenced assets",
        "end_msg": "List of assets printed",
    },
    "verify_assets": {
        "fn": step_verify_assets,
        "start_msg": "Validating asset URLs",
        "end_msg": "Status of all referenced assets checked",
    }
}


def assert_env_exists(step_list):

    load_dotenv(".env")

    failure_list = []
    for step_name in step_list:
        step = step_dict[step_name]
        try:
            for e in step["required_env"]:
                env[e] = getenv(e)
                if env[e] is None:
                    failure_list.append(e)
        except KeyError:
            # It's okay if there are no required envs
            continue

    if len(failure_list) != 0:
        raise Exception(
            f"Required environment variables not found: {failure_list}"
            "maybe you need a .env file?"
        )


def get_yes_no_input(prompt):
    """
    Prompts the user for a 'yes' or 'no' response and keeps asking until a valid answer is given.
    Returns True for 'yes' and False for 'no'.
    """
    while True:
        # Get user input and convert it to lowercase for case-insensitive matching
        user_input = input(f"{prompt} (yes/no): ").lower()

        if user_input in ["yes", "y"]:
            return True
        elif user_input in ["no", "n"]:
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")


def _verify_old_structure():
    deployment_asset_location = safe_getenv("DEPLOYMENT_ASSET_LOCATION", None)
    if deployment_asset_location is None:
        return
    if deployment_asset_location.endswith("resourceGroup"):
        old_structure = safe_getenv("MEDIA_OPS_OLD_STRUCTURE", None)
        if old_structure is None or False:
            if get_yes_no_input(
                "Your DEPLOYMENT_ASSET_LOCATION ends with `resourceGroup` which is "
                "incompatible with the new structure, but MEDIA_OPS_OLD_STRUCTURE is "
                "not set to True. Are you sure you want to continue? (y/n)"
            ):
                return
            else:
                exit()

def get_deployment():
    folder_path = Path("./input/flow_definitions")
    match_list = []
    for file in folder_path.iterdir():
        if not file.is_file():
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                matches = re.findall(
                    r'"name": "deployment",\n\s*"value": "([^"]*)"', content
                )
                match_list += matches
        except Exception as e:
            print(f"Error reading {file}: {e}")
    if len(match_list) == 1:
        return match_list[0]
    elif len(match_list) == 0:
        return None
    else:
        return match_list

def _verify_deployment_asset_location():
    deployment_asset_location = safe_getenv("DEPLOYMENT_ASSET_LOCATION",None)
    if deployment_asset_location is None:
        return

    if deployment_asset_location.endswith("/"):
        print("Please do not end DEPLOYMENT_ASSET_LOCATION with '/'")
        exit()
    try:
        deployment = get_deployment()
    except FileNotFoundError:
        if get_yes_no_input(
            f"The input flow definitions cannot be found at "
            f"./input/flow_definitions so we cannot verify the asset location"
            "\nAre you sure you want to continue? (y/n)"
        ):
            return
        else:
            exit()

    deployment_asset_ending = deployment_asset_location.split('/')[-1]

    if type(deployment) is str:
        if deployment_asset_ending == deployment:
            return
        elif get_yes_no_input(
            f"DEPLOYMENT_ASSET_LOCATION ending {deployment_asset_ending} does not"
            f" match the specified name {deployment}. "
            "Are you sure you want to continue? (y/n)"
        ):
            return
        else:
            exit()

    elif deployment is None:
        if get_yes_no_input(
            "No deployment name found in the sheets, unable to verify the "
            "DEPLOYMENT_ASSET_LOCATION. Are you sure you want to continue? (y/n)"
        ):
            return
        else:
            exit()

    else:
        if get_yes_no_input(
            "DEPLOYMENT_ASSET_LOCATION unable to be verified against input, found:"
            f" {match_list} "
            "Are you sure you want to continue? (y/n)"
        ):
            return
        else:
            exit()


def verify_env(step_list):
    assert_env_exists(step_list)
    _verify_old_structure()
    _verify_deployment_asset_location()


def main(
    step_list,
    dry_run: bool = False,
):
    env["dry_run"] = dry_run

    verify_env(step_list)

    """Main function to orchestrate the entire workflow."""
    print("=" * 50)
    print("🚀 Starting Automated Media Processing Pipeline")
    print("=" * 50)

    for i, step_name in enumerate(step_list):
        step = step_dict[step_name]
        print(f"\n🚀 Step {i+1}: {step['start_msg']}")
        step["fn"]()
        print(f"✅ Step {i+1}: {step['end_msg']}")

    print("\n" + "=" * 50)
    print("🎉 Pipeline execution finished successfully!")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "A script to download assets from Canto, transcode them,"
            " and upload to Google Cloud Storage."
        )
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run. Files will be processed, but not uploaded.",
    )

    parser.add_argument(
        "--steps",
        type=str,
        nargs="+",
        default=["canto_download", "transcode", "firebase_versioned_upload"],
        help=(
            "Space separated list of steps. Defaults to versioned upload pipeline."
            f"\nOptions: {[step_name for step_name in step_dict.keys()]}"
        ),
    )

    args = parser.parse_args()

    main(
        step_list=args.steps,
        dry_run=args.dry_run,
    )
