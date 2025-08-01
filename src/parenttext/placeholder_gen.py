import pathlib
import shutil

import pathlib
import shutil


def create_placeholder_files(file_paths: list[str]):
    """
    Creates placeholder files from a list of destination paths.

    For each path (e.g., 'a/b/c.ext'), it verifies the base directory ('a')
    exists. If so, it creates subdirectories ('a/b/') and copies a template
    from './placeholders/ext.ext' to the destination path.

    Args:
        file_paths: A list of destination file paths.
    """
    placeholder_dir = pathlib.Path('placeholders')
    if not placeholder_dir.is_dir():
        print(f"⚠️  Placeholder directory not found: '{placeholder_dir}'. Aborting.")
        return

    for file_str in file_paths:
        try:
            dest_path = pathlib.Path(file_str)

            # A valid path must have at least a base directory and a filename.
            if len(dest_path.parts) < 2:
                print(f"⚠️  Invalid path format: '{file_str}'. Skipping.")
                continue

            # Verify the base directory for the current file path exists.
            base_dir = pathlib.Path(dest_path.parts[0])
            if not base_dir.is_dir():
                print(f"⚠️  Base directory '{base_dir}' not found. Skipping '{file_str}'.")
                continue

            # Create parent directories (e.g., 'a/b/' from 'a/b/c.ext').
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine the source placeholder from the file extension.
            extension = dest_path.suffix
            if not extension:
                print(f"⚠️  No extension for '{dest_path}'. Skipping file.")
                continue

            # Construct the placeholder path (e.g., 'placeholders/jpg.jpg').
            placeholder_name = f"{extension.lstrip('.')}{extension}"
            source_path = placeholder_dir / placeholder_name

            # Copy the placeholder if it exists.
            if source_path.is_file():
                shutil.copy(source_path, dest_path)
                print(f"✅ Created '{dest_path}'")
            else:
                print(f"⚠️  Placeholder not found: '{source_path}'. Skipping.")

        except Exception as e:
            print(f"❌ Error processing '{file_str}': {e}")


if __name__ == '__main__':
    # --- Example Setup ---
