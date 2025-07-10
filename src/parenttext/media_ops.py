import os
import shutil
import json
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage
from jinja2 import ChainableUndefined, Environment

# Import the actual functions from your provided scripts
from parenttext.canto import main as canto_main
from parenttext.transcode import transcode as transcode_media, prepare as prepare_dir
from parenttext.firebase_tools import Firebase


def main(gcs_base_path, project_id: str | None = None, bucket_name: str | None = None, dry_run: bool=False):
    project_id = project_id or 'idems-media-recorder'
    bucket_name = bucket_name or 'idems-media-recorder.appspot.com'

    """Main function to orchestrate the entire workflow."""
    print("=" * 50)
    print("🚀 Starting Automated Media Processing Pipeline")
    print("=" * 50)


    print("🚀 Step 1: Starting Canto download...")
    
    if Path('canto').exists():
        print(f"  INFO: Removing existing directory '{Path('canto')}' for a clean run.")
        shutil.rmtree(Path('canto'))

    canto_main('canto')
    print("✅ Step 1: Canto download complete.")
        

    print("\n🚀 Step 2: Starting media transcoding...")
    
    # Copy all files into transcoded folder for images & comics
    shutil.copytree('canto', 'transcoded')

    # transcode video & audio
    for fmt in ['video', 'audio']:
        print(f"  -> Transcoding {fmt} folder...")
        raw_dir = f'canto/voiceover/resourceType/{fmt}/'
        video_dir = f'transcoded/voiceover/resourceType/{fmt}/'
        prepare_dir(video_dir, wipe=True)
        transcode_media(raw_dir, video_dir, fmt)
    
    print("✅ Step 2: Transcoding complete.")


    print("\n🚀 Step 3: Starting upload to Firebase Storage...")
    fb = Firebase(project_id=project_id)
    fb.upload_new_version('transcoded', bucket_name, remote_directory=gcs_base_path, dry_run=dry_run)
    print("✅ Step 3: Firebase upload complete.")

    print("\n" + "=" * 50)
    print("🎉 Pipeline execution finished successfully!")
    print("=" * 50)


if __name__ == "__main__":
    gcs_base_path = "project/PLH/subproject/ParentText_v2/deployment/CrisisPalestineTest/resourceGroup"

    main(gcs_base_path=gcs_base_path, dry_run=True)