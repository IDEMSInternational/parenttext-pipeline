import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from rpft.converters import sheets_to_csv

from parenttext_pipeline.cli import load_config
from parenttext_pipeline.pipelines import Config


def init():
    create_archive(load_config())


def create_archive(config: Config):
    for source in config.sources:
        sheet_ids = [sid for sid in source["spreadsheet_ids"]]
        archive_path = Path(config.outputpath) / source["filename"]

        with TemporaryDirectory() as temp_dir:
            sheets_to_csv(temp_dir, sheet_ids)
            filename = shutil.make_archive(archive_path, "zip", temp_dir)

        print(f"Archive created, file={filename}")


if __name__ == "__main__":
    init()
