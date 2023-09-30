import tempfile
import shutil
import os

from parenttext_pipeline.cli import load_config
from rpft.converters import sheets_to_csv

def init():
    create_archive()

def create_archive():
    config = load_config()
    sheet_ids = []
    
    # Read all sheet ids that we want to archive
    for source in config.sources:
        for id in source["spreadsheet_ids"]:
            sheet_ids.append(id)

    archive_path = config.archive_outputpath
    
    temp_dir = tempfile.TemporaryDirectory()
    sheets_to_csv(temp_dir.name, sheet_ids)
    shutil.make_archive(archive_path, 'zip', temp_dir.name)

if __name__ == '__main__':
    init()


