import argparse
import subprocess
import shutil
from pathlib import Path


def start():
    args = parse_args()
    transcode(args.source, prepare(args.destination, wipe=True), args.format)


def parse_args():
    parser = argparse.ArgumentParser(
        description=("Transcode videos to ParentText specification"),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "source",
        help=("directory containing source video files"),
    )
    parser.add_argument(
        "destination",
        help=("directory where transcoded videos will be saved"),
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
    op = {"video": to_video, "audio": to_audio}[fmt]
    sources = list(src_root.glob("**/*.mp4"))
    count = len(sources)

    print("Source files found,", {"count": count})

    for i, video_src in enumerate(sources, start=1):
        file_dst = dst_root / video_src.relative_to(src_root)
        prepare(file_dst.parent)
        final_dst = op(video_src, file_dst)
        print(
            "Operation completed,",
            {
                "op": op.__name__,
                "source": str(video_src),
                "dest": str(final_dst),
                "progress": f"{i}/{count}",
            },
        )

def transcode_audio_only(src, dst):
    """
    Transcodes all audio files in the source directory to MP3 format using
    the same settings as `to_audio`, preserving folder structure.
    """
    src_root = Path(src)
    dst_root = Path(dst)

    audio_extensions = [".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp3"]
    sources = [p for ext in audio_extensions for p in src_root.rglob(f"*{ext}")]
    count = len(sources)

    print("Audio source files found,", {"count": count})

    for i, audio_src in enumerate(sources, start=1):
        rel_path = audio_src.relative_to(src_root)
        file_dst = dst_root / rel_path
        prepare(file_dst.parent)
        final_dst = to_audio(audio_src, file_dst)
        print(
            "Audio transcoding completed,",
            {
                "source": str(audio_src),
                "dest": str(final_dst),
                "progress": f"{i}/{count}",
            },
        )


def to_video(src: Path, dst: Path):
    first_pass(src)
    second_pass(src, dst)

    return dst


def to_audio(src: Path, dst: Path):
    final_dst = dst.with_suffix(".mp3")
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
        + [str(final_dst)],
    )

    return final_dst


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


if __name__ == "__main__":
    start()
