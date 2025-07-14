import os
import shutil


def rearrange_folders(source_dir, dest_dir):
    """
    Rearranges files from a source directory to a new structure in a destination directory.

    Args:
        source_dir (str): The path to the directory with the original file structure.
        dest_dir (str): The path to the directory where the new structure will be created.
    """
    # A mapping for language folders to language codes.
    # You can add more mappings here, e.g., {'Espanol': 'spa'}
    languages = [
        "ara", "eng", "msa",
    ]

    # --- 1. Create the new directory structure ---
    print("Creating the new directory structure...")

    # Create image and comic directories
    image_universal_path = os.path.join(dest_dir, "image", "universal")
    os.makedirs(image_universal_path, exist_ok=True)

    comic_path = os.path.join(dest_dir, "comic")
    os.makedirs(comic_path, exist_ok=True)

    # Create the nested voiceover structure
    base_voiceover_path = os.path.join(dest_dir, "voiceover", "resourceType")
    for resource_type in ["video", "audio"]:
        for gender in ["male", "female"]:
            for lang_code in set(languages):  # Creates eng, spa, etc.
                os.makedirs(
                    os.path.join(
                        base_voiceover_path,
                        resource_type,
                        "gender",
                        gender,
                        "language",
                        lang_code,
                    ),
                    exist_ok=True,
                )

    print("New directory structure created successfully.\n")

    # --- 2. Walk through the source directory and move files ---
    print("Moving files...")
    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            source_file_path = os.path.join(dirpath, filename)

            # Use os.path.normpath to handle different OS path separators
            # and then split
            path_parts = os.path.normpath(source_file_path).split(os.sep)

            # We are interested in paths that have enough parts to process
            if len(path_parts) > 1:
                top_level_folder = path_parts[1].lower()

                # --- Handle Image Files ---
                if top_level_folder == "image":
                    new_filename = filename.lower()
                    dest_path = os.path.join(image_universal_path, new_filename)
                    print(f"Moving {source_file_path} to {dest_path}")
                    shutil.move(source_file_path, dest_path)

                # --- Handle Audio and Video Files ---
                elif top_level_folder in ["audio", "video"]:
                    if len(path_parts) >= 5:  # source_root/Audio/Female/Ara/file.m4a
                        resource_type = path_parts[1].lower()
                        gender = path_parts[2].lower()
                        lang_folder = path_parts[3].lower()
                        lang_code = path_parts[4].lower()

                        if lang_code != "unknown":
                            dest_folder = os.path.join(
                                base_voiceover_path,
                                resource_type,
                                "gender",
                                gender,
                                "language",
                                lang_code,
                            )
                            new_filename = filename.lower()
                            dest_path = os.path.join(dest_folder, new_filename)
                            print(f"Moving {source_file_path} to {dest_path}")
                            shutil.move(source_file_path, dest_path)
                        else:
                            print(
                                f"Warning: No language mapping for folder '{lang_folder}' in '{source_file_path}'. Skipping file."
                            )
                    else:
                        print(
                            f"Warning: File '{source_file_path}' is in an unexpected subdirectory. Skipping."
                        )

    print("\nFile rearrangement complete!")


if __name__ == "__main__":
    source_root = input(
        "type the /path/to/your/original/folder: "
    )  # e.g., 'C:/Users/YourUser/Desktop/Original'
    destination_root = input(
        "type the /path/to/your/new/folder: "
    )  # e.g., 'C:/Users/YourUser/Desktop/Rearranged'

    # Check if the source directory exists before running
    if os.path.isdir(source_root):
        rearrange_folders(source_root, destination_root)
    else:
        print(f"Error: The source directory '{source_root}' does not exist.")
        print(
            "Please create a dummy folder and files or update the path to your actual source folder."
        )
