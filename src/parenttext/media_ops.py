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
from pathlib import Path
from dotenv import load_dotenv
from os import getenv

# Import the actual functions from your provided scripts
from parenttext.canto import main as canto_main
from parenttext.transcode import transcode as transcode_media, prepare as prepare_dir
from parenttext.firebase_tools import Firebase

from parenttext.referenced_assets import get_referenced_assets, get_parenttext_paths
from parenttext.placeholder_gen import create_placeholder_files


env = {}


def safe_getenv(key, default):
    if key not in env.keys():
        env[key] = getenv(key)

    if env[key] is None:
        env[key] = default
    
    return env[key]


def step_canto_download():
    if Path("canto").exists():
        # Copy all files into transcoded folder for images & comics
        shutil.copytree("canto", "old_canto")
        print(f"  INFO: Removing existing directory '{Path('canto')}' for a clean run.")
        shutil.rmtree(Path("canto"))

    canto_main("canto")


def step_transcode():

    transcode_path = safe_getenv("MEDIA_OPS_TRANSCODE_FOLDER", "transcoded")

    # Copy all files into transcoded folder for images & comics
    # TODO: Handle compression of these folders in below loop with transcode
    try:
        shutil.copytree("canto/image", f"{transcode_path}/image", dirs_exist_ok=True)
        shutil.copytree("canto/comic", f"{transcode_path}/comic", dirs_exist_ok=True)
    except FileNotFoundError:
        print("  Warning: Image/Comic split not found, skipping")

    # transcode video & audio
    for fmt in ["video", "audio"]:
        print(f"  -> Transcoding {fmt} folder...")
        raw_dir = f"canto/voiceover/resourceType/{fmt}/"
        # Handle case where audio is transcoded from video source
        if not Path(raw_dir).exists() and fmt == "audio":
            print("  Transcoding audio from video files.")
            raw_dir = "canto/voiceover/resourceType/video/"
        old_dir = f"old_{raw_dir}"
        transcoded_dir = f"{transcode_path}/voiceover/resourceType/{fmt}/"
        prepare_dir(transcoded_dir, wipe=False)  # make dir if doesn't exist
        transcode_media(raw_dir, transcoded_dir, old_src=old_dir, fmt=fmt)

    # remove old canto directory once it's no longer needed for change detection
    shutil.rmtree(Path("old_canto"))

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


def step_placeholder_gen():

    rapidpro_file = safe_getenv("RAPIDPRO_OUTPUT", "./output/parenttext_all.json")
    placeholder_directory = safe_getenv(
        "MEDIA_OPS_PLACEHOLDER_FOLDER", "placeholder_assets"
    )

    with open("config.json", "r") as fh:
        language_dicts = json.load(fh)["sources"]["translation"]["languages"]
    language_list = [d["language"] for d in language_dicts]

    gender_list = ["male", "female"]  # Sexs will be replaced with genders soon...

    path_dict = get_parenttext_paths(placeholder_directory, language_list, gender_list)

    asset_list = get_referenced_assets(rapidpro_file, path_dict)

    create_placeholder_files(asset_list)

    env["MEDIA_OPS_UPLOAD_FOLDER"] = placeholder_directory


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


def main(
    step_list,
    dry_run: bool = False,
):
    env["dry_run"] = dry_run

    assert_env_exists(step_list)

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
