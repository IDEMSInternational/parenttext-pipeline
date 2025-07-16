import argparse
import shutil
import json
from pathlib import Path

# Import the actual functions from your provided scripts
from parenttext.canto import main as canto_main
from parenttext.transcode import transcode as transcode_media, prepare as prepare_dir
from parenttext.firebase_tools import Firebase


def main(
    config_file: str | None = None,
    gcs_base_path: str | None = None,
    project_id: str | None = None,
    bucket_name: str | None = None,
    dry_run: bool = False,
):
    with open(config_file or "config.json", "r") as fh:
        config = json.load(fh)["sources"]["deployment_storage"]

    gcs_base_path = gcs_base_path or config["location"]
    project_id = project_id or config["annotations"]["project_id"]
    bucket_name = bucket_name or config["annotations"]["bucket_name"]

    """Main function to orchestrate the entire workflow."""
    print("=" * 50)
    print("🚀 Starting Automated Media Processing Pipeline")
    print("=" * 50)

    print("🚀 Step 1: Starting Canto download...")

    if Path("canto").exists():
        print(f"  INFO: Removing existing directory '{Path('canto')}' for a clean run.")
        shutil.rmtree(Path("canto"))

    canto_main("canto")
    print("✅ Step 1: Canto download complete.")

    print("\n🚀 Step 2: Starting media transcoding...")

    # Copy all files into transcoded folder for images & comics
    shutil.copytree("canto", "transcoded")

    # transcode video & audio
    for fmt in ["video", "audio"]:
        print(f"  -> Transcoding {fmt} folder...")
        raw_dir = f"canto/voiceover/resourceType/{fmt}/"
        if not Path(raw_dir).exists() and fmt == "audio":
            print("  Transcoding audio from video files.")
            raw_dir = f"canto/voiceover/resourceType/video/"
        transcoded_dir = f"transcoded/voiceover/resourceType/{fmt}/"
        prepare_dir(transcoded_dir, wipe=True)
        transcode_media(raw_dir, transcoded_dir, fmt)

    print("✅ Step 2: Transcoding complete.")

    print("\n🚀 Step 3: Starting upload to Firebase Storage...")
    fb = Firebase(project_id=project_id)
    fb.upload_new_version(
        "transcoded", bucket_name, remote_directory=gcs_base_path, dry_run=dry_run
    )
    print("✅ Step 3: Firebase upload complete.")

    print("\n" + "=" * 50)
    print("🎉 Pipeline execution finished successfully!")
    print("=" * 50)


if __name__ == "__main__":
    # 1. Initialize the Argument Parser
    parser = argparse.ArgumentParser(
        description="A script to download assets from Canto, transcode them, and upload to Google Cloud Storage."
    )

    # 2. Define Command-Line Arguments
    parser.add_argument(
        "--gcs_base_path",
        type=str,
        help="The base path in Google Cloud Storage for the upload (e.g., 'v1/en').",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default="idems-media-recorder",
        help="The target Firebase project ID.",
    )
    parser.add_argument(
        "--bucket-name",
        type=str,
        default="idems-media-recorder.appspot.com",
        help="The target Firebase Storage bucket name.",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run. Files will be processed, but not uploaded.",
    )

    # 3. Parse the arguments from the command line
    args = parser.parse_args()

    # 4. Call the main function with the parsed arguments
    main(
        gcs_base_path=args.gcs_base_path,
        project_id=args.project_id,
        bucket_name=args.bucket_name,
        dry_run=args.dry_run,
    )
