import argparse
import subprocess
import shutil
from pathlib import Path


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


def transcode(src, dst, fmt="video"):
    src_root = Path(src)
    dst_root = Path(dst)
    exts = INPUT_EXTS[fmt]
    sources = [p for ext in exts for p in src_root.rglob(f"*.{ext}")]
    count = len(sources)
    op = OPS[fmt]

    print("Source files found,", {"count": count})

    for i, source in enumerate(sources, start=1):
        file_dst = dst_root / source.relative_to(src_root)
        prepare(file_dst.parent)
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
}


if __name__ == "__main__":
    start()
