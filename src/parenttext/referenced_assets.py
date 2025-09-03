import json
import re
import itertools


def _get_attachments(rapidpro_json):
    for flow in rapidpro_json["flows"]:
        for node in flow["nodes"]:
            for action in node["actions"]:
                if "attachments" in action.keys():
                    if action["attachments"] != []:
                        yield action["attachments"]


def process_attachment(attachment, path_dict, method) -> list:
    match method:
        case "parenttext":
            try:
                file = re.findall(r'& "(.*)"\)', attachment)[0]
                path = re.findall(r"fields\.(.*) &", attachment)[0]
                return ["/".join([p, file]) for p in path_dict[path]]
            except IndexError:
                pass
            except KeyError:
                print(f"Was unable to process path {path}, associated with file {file}")
    # If the method failed, print and return
    print(f"Could not process attachment {attachment}")
    return [attachment]


def clean_path_dict(path_dict):
    return {key: [i.rstrip("/") for i in val_ls] for key, val_ls in path_dict.items()}


def get_referenced_assets(rapidpro_file, path_dict, process_attachment_method=None):
    process_attachment_method = process_attachment_method or "parenttext"

    path_dict = clean_path_dict(path_dict)

    with open(rapidpro_file, "r", errors="ignore") as f:
        rapidpro_json = json.load(f)

    attachments = [
        item
        for sublist in _get_attachments(rapidpro_json)
        for item in sublist
        if sublist
    ]
    unique_attachments = list(set(attachments))

    referenced_assets = []
    for a in unique_attachments:
        referenced_assets += process_attachment(
            a, path_dict, method=process_attachment_method
        )

    return referenced_assets


def get_parenttext_paths(root, language_list, gender_list, folder_versions=None, old_structure=False):
    _folder_versions = {"logo": "", "comic": "", "image": "", "voiceover": ""}
    if folder_versions is not None:
        _folder_versions.update(folder_versions)
    versioned_folder = {k: "".join([k, v]) for k, v in _folder_versions.items()}

    root = root.rstrip("/")
    path_dict = {
        "path": [root],
        "comic_path": ["/".join([root, versioned_folder["comic"]])],
        "logo_path": ["/".join([root, versioned_folder["logo"]])],
    }
    if old_structure:
        path_dict["image_path"] = ["/".join([root, versioned_folder["image"], "universal"])]
    else:
        path_dict["image_path"] = ["/".join([root, versioned_folder["image"]])]

    av_tails = []
    for gender, language in itertools.product(gender_list, language_list):
        if old_structure:
            av_tails.append("/".join(["gender", gender, "language", language]))
        else:
            av_tails.append("/".join([gender, language]))

    path_dict["voiceover_video_path"] = []
    path_dict["voiceover_audio_path"] = []
    for tail in av_tails:
        if old_structure:
            path_dict["voiceover_video_path"].append(
                "/".join(
                    [root, versioned_folder["voiceover"], "resourceType", "video", tail]
                )
            )
            path_dict["voiceover_audio_path"].append(
                "/".join(
                    [root, versioned_folder["voiceover"], "resourceType", "audio", tail]
                )
            )
        else:
            path_dict["voiceover_video_path"].append(
                "/".join(
                    [root, versioned_folder["voiceover"], "video", tail]
                )
            )
            path_dict["voiceover_audio_path"].append(
                "/".join(
                    [root, versioned_folder["voiceover"], "audio", tail]
                )
            )            

    return path_dict
