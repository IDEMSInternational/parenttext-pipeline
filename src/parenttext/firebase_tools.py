from pathlib import Path
import hashlib
import base64
import re
import uuid
from google.cloud import storage
from rpft.google import get_credentials


class Firebase:
    gcs_client: storage.Client  # Get the typing right

    def __init__(
        self,
        project_id: str,
        key_path: str | None = None,
        credentials_file: str | None = None,
        token_file: str | None = None,
    ) -> None:
        """
        Initializes the Firebase tool.

        Args:
            project_id (str): Your Google Cloud project ID.
            key_path (str | None): Path to the service account JSON key file.
            credentials_file (str | None): Path to the OAuth 2.0 client_secrets.json file.
            token_file (str | None): Path to the authorized user token.json file.
        """

        gcs_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        self.project_id = project_id
        self.creds = get_credentials(scopes=gcs_scopes)
        self.gcs_client = storage.Client(project=self.project_id, credentials=self.creds)

    def get_latest_folder_version(self, bucket_name, gcs_base_path) -> int:
        """Get latest folder version, if folder doesn't exist, return -1.

        Parameters
        ----------
        bucket_name : _type_
            _description_
        gcs_base_path : _type_
            _description_

        Returns
        -------
        int
            _description_
        """
        # --- Find latest matching directory on the remote ---
        blob_list = list(self.gcs_client.list_blobs(bucket_name, prefix=gcs_base_path))

        search_pattern = rf"^{gcs_base_path.rstrip('/')}(\d*)/.*$"
        remote_version_number = -1  # initialize at -1
        # Get v out as a capture group
        capture_list = [re.findall(search_pattern, blob.name)[0] for blob in blob_list]

        # Iterate through unique captures
        for v in list(set(capture_list)):
            if v == "" and remote_version_number == -1:
                remote_version_number = 1
            # Save the highest number
            elif int(v) > remote_version_number:
                remote_version_number = int(v)

        return remote_version_number

    def upload_new_version(
        self,
        source_directory,
        bucket_name,
        remote_directory,
        version_level: int = 1,
        dry_run: bool = False,
    ):

        current_versions = {}
        base_path = Path(source_directory)

        # Create a glob pattern for the specific depth, e.g., "*/*" for version_level=2
        pattern = "/".join(["*"] * version_level)

        # Check each path at the given level:
        # Use rglob to find all matching directories
        for version_folder in base_path.glob(pattern):
            if not version_folder.is_dir():  # not a version folder
                print(f"Warning, skipping file {version_folder}")
                continue
            vfp = "/".join(version_folder.parts[1:])
            print(f"Comparing hashes in {vfp}")

            remote_folder_path = "/".join([remote_directory.rstrip("/"), vfp])
            # Get latest version
            remote_version_number = self.get_latest_folder_version(
                bucket_name, remote_folder_path
            )
            match remote_version_number:
                case 1:
                    remote_version_str = ""
                case -1:
                    raise NotImplementedError(
                        "Remote version-level folder doesn't exist. " \
                        "Should only happen during new upload. " \
                        "TODO: Figure out how to handle new uploads"
                    )
                case _:
                    remote_version_str = str(remote_version_number)
            remote_version_folder = Path(f"{remote_folder_path}{remote_version_str}/")

            up_to_date = True
            for file_path in version_folder.rglob("*"):
                if not file_path.is_file():
                    continue

                remote_file_path = (
                    remote_version_folder / file_path.relative_to(version_folder)
                ).as_posix()
                try:
                    hash_match = self.compare_hashes(
                        file_path, bucket_name, remote_file_path
                    )
                except Exception as e:
                    print(e)
                    hash_match = False

                if not hash_match:
                    print(f"Hash mismatch: {file_path}")
                    up_to_date = False
                    break

            if not up_to_date:
                remote_version_number += 1
                print(
                    f"Bumping {version_folder.relative_to(source_directory).as_posix()} to {remote_version_number}"
                )
                # Bump the remote version number
                remote_version_folder = Path(
                    f"{version_folder.relative_to(source_directory).as_posix()}{remote_version_number}"
                )
                self.upload_folder(
                    bucket_name,
                    local_base_path=(version_folder),
                    gcs_base_path=(remote_directory / remote_version_folder).as_posix(),
                    dry_run=dry_run,
                )
            else:
                print(f"Hashes Matched for {version_folder.relative_to(source_directory).as_posix()}")
            current_versions[
                version_folder.relative_to(source_directory).as_posix()
            ] = remote_version_number
        print("Current Versions")
        print(current_versions)

    def compare_hashes(self, local_filepath, bucket_name, file_path_in_storage):
        """Compares the MD5 hash of a local file with a Firebase Storage file."""

        # Calculate local hash
        hasher = hashlib.md5()
        with open(local_filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        local_hash = hasher.hexdigest()

        bucket = self.gcs_client.bucket(bucket_name)
        blob_name = file_path_in_storage  # TODO conversion
        blob = bucket.blob(blob_name)

        # Fetch the blob's metadata
        blob.reload()

        if blob.md5_hash:
            # The md5_hash property is base64 encoded.
            # Decode and then optionally hex encode for common representation.
            decoded_md5 = base64.b64decode(blob.md5_hash)
            remote_hash = decoded_md5.hex()
        else:
            print(
                f"MD5 hash not available for object {blob_name} in bucket {bucket_name}."
            )
            return False

        return local_hash == remote_hash

    def upload_folder(self, bucket_name, local_base_path, gcs_base_path, dry_run=False):
        """Recursively uploads files from a local folder to a GCS bucket."""
        bucket = self.gcs_client.bucket(bucket_name)

        local_folder_as_path = Path(local_base_path)

        for file_path in local_folder_as_path.rglob(
            "*"
        ):  # Recursively iterates through files and subdirectories
            if file_path.is_file():
                # Construct the destination blob name based on the relative path
                destination_blob_name = (
                    gcs_base_path / file_path.relative_to(local_folder_as_path)
                ).as_posix()
                if not dry_run:
                    blob = bucket.blob(destination_blob_name)

                    # Upload File
                    blob.upload_from_filename(str(file_path))
                    # Generate Token to allow access to the file
                    access_token = uuid.uuid4()
                    # Update metadata with the new token
                    metadata = {'firebaseStorageDownloadTokens': access_token}
                    blob.metadata = metadata
                    # Use patch() to update the metadata on the object
                    blob.patch()
                    # Make the blob publicly readable
                    blob.make_public()
                else:
                    print("Dry Run")
                print(
                    f"Uploaded {file_path} to gs://{bucket_name}/{destination_blob_name}"
                )


if __name__ == "__main__":
    bucket_name = "idems-media-recorder.appspot.com"

    prefix = (
        "project/PLH/subproject/ParentText_v2/deployment/CrisisPalestine/resourceGroup/"
    )

    fb = Firebase(project_id="idems-media-recorder")
    blobs = fb.gcs_client.list_blobs(bucket_name, prefix=prefix)
