import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import requests
from dotenv import load_dotenv
from jinja2 import ChainableUndefined, Environment


@dataclass
class MediaAsset:
    format: str
    id: str
    language: str
    name: str
    folder: str
    annotations: dict = field(default_factory=dict)


img_fmt = "jpg"
img_dim_lim = 2000


class Canto:

    def __init__(
        self,
        app_id,
        app_secret,
        user_id,
        site_base_url,
        mappings={},
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.user_id = user_id
        self.oauth_base_url = (
            "https://oauth." + site_base_url.split("//")[-1].split(".", 1)[-1]
        )
        self.site_base_url = site_base_url
        self.mappings = mappings
        self._token = None

    @property
    def token(self):
        if not self._token:
            self._token = self.authorize()

        return self._token

    def authorize(self):
        return (
            requests.request(
                "POST",
                f"{self.oauth_base_url}/oauth/api/oauth2/compatible/token",
                data={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret,
                    "grant_type": "client_credentials",
                    "user_id": self.user_id,
                },
            )
            .json()
            .get("access_token")
        )

    def tree(self, folder_id: str):
        req = requests.request(
            method="GET",
            url=f"{self.site_base_url}/api/v1/tree/{folder_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        if req.status_code == 401:
            raise Exception("401 Unauthorized: Ensure environment variables are loaded")
        return req.json().get("results", [])

    def album(self, album_id: str):
        return (
            requests.request(
                method="GET",
                url=f"{self.site_base_url}/api/v1/album/{album_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            .json()
            .get("results", [])
        )

    def download(self, scheme: str, content_id: str):
        if scheme == "image":
            return self._download_image(scheme, content_id)

        return requests.request(
            method="GET",
            url=f"{self.site_base_url}/api_binary/v1/{scheme}/{content_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        ).content

    def _download_image(self, scheme, content_id: str):
        url = f"{self.site_base_url}/api/v1/{scheme}/{content_id}"
        metadata = json.loads(
            requests.request(
                method="GET",
                url=url,
                headers={"Authorization": f"Bearer {self.token}"},
            ).content
        )
        width = int(metadata["width"])
        height = int(metadata["height"])
        if max(width, height) > img_dim_lim:
            ratio = img_dim_lim / max(width, height)
        else:
            ratio = 1

        advdownload = f"download?resize={int(width * ratio)}x{int(height * ratio)}&dpi=72&type={img_fmt}&proportion=true"
        url = f"{self.site_base_url}/api_binary/v1/advance/{scheme}/{content_id}/{advdownload}"
        return requests.request(
            method="GET",
            url=url,
            headers={"Authorization": f"Bearer {self.token}"},
        ).content

    def list_assets(self, tree):
        for item in tree:

            if item["scheme"] == "album":

                for content in self.album(item["id"]):
                    annotations = transform_values(
                        self.mappings,
                        content.get("additional", {}),
                    )
                    asset = MediaAsset(
                        annotations=annotations,
                        format=content["scheme"],
                        id=content["id"],
                        language=annotations.get("Language", [""])[0],
                        name=content["name"],
                        folder=item["name"],
                    )
                    yield asset

            if item["scheme"] == "folder":
                yield from self.list_assets(item["children"])


def transform_values(mappings: dict, d: dict) -> dict:
    transformed = {}

    for k, v in d.items():
        m = mappings.get(k) or {}

        if isinstance(v, list):
            transformed[k] = [m.get(item, item) for item in v]
        else:
            transformed[k] = m.get(v, v)

    return transformed


def asset_path(path_template, asset: MediaAsset):
    asset_dict = asdict(asset)
    if asset_dict["format"] == "image":
        asset_dict["name"] = str(Path(asset_dict["name"]).with_suffix("." + img_fmt))

    return os.path.normpath(path_template.render(**asset_dict))


def download_all(client, path_template, location: str, destination: str):
    tree = client.tree(location)

    for asset in client.list_assets(tree):
        download(client, path_template, asset, destination)


def download(client, path_template, asset: MediaAsset, destination):
    dst = Path(destination) / asset_path(path_template, asset)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        print(f"Download skipped, path={dst}")
        return

    with open(dst, "wb") as fh:
        fh.write(client.download(asset.format, asset.id))

    print(f"Download completed, path={dst}")


def main(destination: str, config_file: str | None = None):
    with open(config_file or "config.json", "r") as fh:
        config = json.load(fh)["sources"]["media_assets"]

    _env = Environment(undefined=ChainableUndefined)
    if not load_dotenv(".env"):
        print("You likely need a .env file in current working directory")

    download_all(
        client=Canto(
            app_id=os.getenv("CANTO_APP_ID"),
            app_secret=os.getenv("CANTO_APP_SECRET"),
            user_id=os.getenv("CANTO_USER_ID"),
            site_base_url=config["storage"]["annotations"]["site_base_url"],
            mappings=config.get("mappings") or {},
        ),
        path_template=_env.from_string(os.path.join(*config["path_template"])),
        location=config["storage"]["location"],
        destination=destination,
    )


if __name__ == "__main__":
    main(destination=sys.argv[1])
