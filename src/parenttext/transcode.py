import argparse
import subprocess
import shutil
from pathlib import Path
import hashlib
import json
from parenttext.firebase_tools import Firebase


AUDIO_EXTS = [
    "aac",
    "flac",
    "m4a",
    "mp3",
    "ogg",
    "wav",
]
VIDEO_EXTS = [
    "avi",
    "mp4",
]
INPUT_EXTS = {
    "audio": AUDIO_EXTS + VIDEO_EXTS,
    "video": VIDEO_EXTS,
}


def start():
    args = parse_args()
    transcode(args.source, prepare(args.destination, wipe=True), args.format)


def parse_args():
    parser = argparse.ArgumentParser(
        description=("Transcode audio/video to ParentText specification"),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "source",
        help=("directory containing source files"),
    )
    parser.add_argument(
        "destination",
        help=("directory where transcoded files will be saved"),
    )
    parser.add_argument(
        "-f",
        "--format",
        default="video",
        choices=["audio", "video"],
        help=(
            "output format (default: 'video'); 'audio' extracts audio only from source"
            " videos and saves as MP3"
        ),
    )

    return parser.parse_args()


def prepare(dst, wipe=False):
    dest = Path(dst)

    if wipe and dest.exists():
        shutil.rmtree(dest)
        print("Directory deleted,", {"path": str(dest)})

    if not dest.exists():
        dest.mkdir(parents=True)
        print("Directory created,", {"path": str(dest)})

    return dst


def source_has_changed(file_dst, source, old_file=None):
    """Compare the MD5 hashes of a file with its old version if it exists."""
    if file_dst.exists() and old_file is not None:
        if old_file.exists():
            with open(source, "rb") as f:
                new_hash = hashlib.md5(f.read()).hexdigest()
            with open(old_file, "rb") as f:
                old_hash = hashlib.md5(f.read()).hexdigest()
            if new_hash == old_hash:
                return False
    return True


def transcode(src, dst, old_src=None, fmt="video"):
    src_root = Path(src)
    dst_root = Path(dst)
    old_src_root = Path(old_src) if old_src else None
    exts = INPUT_EXTS[fmt]
    sources = [p for ext in exts for p in src_root.rglob(f"*.{ext}")]
    count = len(sources)
    op = OPS[fmt]

    print("Source files found,", {"count": count})

    for i, source in enumerate(sources, start=1):
        file_dst = dst_root / source.relative_to(src_root)
        prepare(file_dst.parent)
        old_file = old_src_root / source.relative_to(src_root) if old_src_root else None
        # Compare if file has changed from old source to avoid retranscoding
        if not source_has_changed(file_dst, source, old_file):
            print(f"Skipping unchanged file: {source}")
            continue

        final_dst = op(source, file_dst)
        print(
            "Operation completed,",
            {
                "op": op.__name__,
                "source": str(source),
                "dest": str(final_dst),
                "progress": f"{i}/{count}",
            },
        )


def transcode_dir(src, dst, env, audio_from_video=True, old_structure=False):
    fb = Firebase(project_id=env["GCS_PROJECT_ID"])
    try:
        hash_manifest = fb.download_hash_manifest(
            bucket_name=env["GCS_BUCKET_NAME"],
            remote_directory=env["DEPLOYMENT_ASSET_LOCATION"],
        )
    except Exception as e:
        print(e)
        hash_manifest = {}
    resource_type = "resourceType/" if old_structure else ""

    if audio_from_video:
        shutil.copytree(src / "voiceover" / "video", src / "voiceover" / "audio", dirs_exist_ok=True)
    hash_manifest.update(handle_dir(src=Path(src), dst=Path(dst), env=env, fb=fb, hash_manifest=hash_manifest, resource_type=resource_type))
    # write hash_manifest to a local file for future reference
    with open(dst / "hash_manifest.json", "w") as f:
        json.dump(hash_manifest, f, indent=4)


def handle_dir(src: Path, dst: Path, env: dict, fb: Firebase, hash_manifest: dict, resource_type: str):
    for dir in src.iterdir():
        if dir.is_dir():
            if dir.name in OPS:
                op = OPS[dir.name]
                sources = [p for p in dir.rglob("*") if p.is_file()]
                count = len(sources)
                print(f"Processing {dir.name} files, found {count} files.")
                relative_dir = dir.relative_to([p for p in dir.parents][-2])
                for i, source in enumerate(sources, start=1):
                    filename = source.relative_to(dir)
                    relative_path = source.relative_to(src)
                    key = str(relative_dir / filename).replace("\\", "/")  # Normalize for Windows paths
                    file_dst = dst / relative_path
                    prepare(file_dst.parent)
                    source_hash = hashlib.md5(source.read_bytes()).hexdigest()
                    if hash_manifest and key in hash_manifest:
                        if hash_manifest[key] == source_hash:
                            # File has not changed, download from Firebase
                            source_blob_name = fb.get_latest_path(
                                bucket_name=env["GCS_BUCKET_NAME"],
                                gcs_base_path=env["DEPLOYMENT_ASSET_LOCATION"],
                                path_in_dir=key,
                            )
                            fb.download_file(
                                bucket_name=env["GCS_BUCKET_NAME"],
                                source_blob_name=source_blob_name,
                                destination_file_name=str(file_dst),
                            )
                            print(f"Downloaded unchanged file from Firebase: {source}")
                            continue
                    # File has changed or not in manifest, transcode
                    
                    hash_manifest[key] = source_hash
                    final_dst = op(source, file_dst)
                    print(
                        "Operation completed,",
                        {
                            "op": op.__name__,
                            "source": str(source),
                            "dest": str(final_dst),
                            "progress": f"{i}/{count}",
                        },
                    )
            else:
                # Recurse into the directory
                hash_manifest.update(handle_dir(src=dir, dst=dst / dir.name, env=env, fb=fb, hash_manifest=hash_manifest, resource_type=resource_type))

    return hash_manifest


def to_video(src: Path, dst: Path):
    out = dst.with_suffix(".mp4")
    first_pass(src)
    second_pass(src, out)

    return dst


def to_audio(src: Path, dst: Path):
    out = dst.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg"]
        + ["-y"]
        + ["-loglevel", "warning"]
        + ["-i", str(src)]
        + ["-c:a", "mp3"]
        + ["-b:a", "64k"]
        + ["-ar", "48k"]
        + ["-ac", "1"]
        + ["-f", "mp3"]
        + [str(out)],
    )

    return out


def copy(src: Path, dst: Path):
    out = dst
    shutil.copyfile(src, dst)
    return out


def first_pass(src):
    subprocess.run(
        ["ffmpeg"]
        + ["-y"]
        + ["-loglevel", "warning"]
        + ["-i", str(src)]
        + ["-c:v", "libx264"]
        + ["-r:v", "20"]
        + ["-s:v", "720x406"]
        + ["-b:v", "84k"]
        + ["-profile:v", "baseline"]
        + ["-pass", "1"]
        + ["-an"]
        + ["-f", "null"]
        + ["/dev/null"],
    )


def second_pass(src, dst):
    subprocess.run(
        ["ffmpeg"]
        + ["-y"]
        + ["-loglevel", "warning"]
        + ["-i", str(src)]
        + ["-c:v", "libx264"]
        + ["-r:v", "20"]
        + ["-s:v", "720x406"]
        + ["-b:v", "84k"]
        + ["-profile:v", "baseline"]
        + ["-pass", "2"]
        + ["-c:a", "aac"]
        + ["-b:a", "42k"]
        + ["-ar", "24k"]
        + ["-ac", "1"]
        + ["-f", "mp4"]
        + [str(dst)],
    )


OPS = {
    "video": to_video,
    "audio": to_audio,
    "image": copy,
    "comic": copy,
    "logo": copy,
}


if __name__ == "__main__":
    start()
