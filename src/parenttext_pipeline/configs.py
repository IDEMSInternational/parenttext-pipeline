from dataclasses import dataclass, field
import json
from pathlib import Path
import contextlib
import os
import runpy

from parenttext_pipeline.config_converter import convert_config


@dataclass(kw_only=True)
class StepConfig:
    # Identifier (name) of the step
    id: str
    # Type of the step, should be one of STEP_CONFIGS.keys()
    # Make this an enum maybe
    type: str
    # A list of input data sources used by this step
    sources: list = field(default_factory=list)


@dataclass(kw_only=True)
class CreateFlowsStepConfig(StepConfig):
    # Name of the Python module containing data models describing the data sheets
    models_module: str = None
    # Tags for RPFT create_flows operation
    tags: list


@dataclass(kw_only=True)
class SafeguardingStepConfig(StepConfig):
    # Either (flow_id and flow_name) or redirect_flow_names has to be provided

    # The UUID of the RapidPro flow for safeguarding.
    flow_uuid: str = None
    # The name of the RapidPro flow for safeguarding.
    flow_name: str = None
    # A string representing a list of flow names o_O
    # Names of redirect flows to be modified as part of safeguarding process.
    redirect_flow_names: str


@dataclass(kw_only=True)
class UpdateExpirationStepConfig(StepConfig):
    # Default flow expiration time
    default_expiration_time: int
    # sources: may reference a JSON-type source defining a file_dict containing
    # the following key: `special_expiration_file`.
    # This source file maps flow names to expiration times


@dataclass(kw_only=True)
class QRTreatmentStepConfig(StepConfig):

    # str: how to process quick replies
    # move: Remove quick replies and add equivalents to them to the message text,
    #     and give numerical prompts to allow basic phone users to use the app.
    # move_and_mod: As above but has additional functionality allowing you
    #     to replace phrases
    # reformat: Reformat quick replies so that long ones are added to the message text,
    #     as above.
    # reformat_whatsapp: Reformat quick replies to meet the length and message
    #                    restrictions of whatsapp
    # reformat_palestine: Reformat quick replies to the standard as needed by Palestine
    # reformat_china: Reformat quick replies to the standard as requested by China
    # wechat: All quick replies moved to links in message text as can be used in WeChat
    qr_treatment: str

    # When qr_treatment is 'reformat',
    # set limits on the number of quick replies that are processed.
    # If the number of quick replies is below or equal to count_threshold
    # then the quick replies are left in place.
    count_threshold: str = None

    # When qr_treatment is 'reformat', set limits on the number of quick replies
    # that are processed. If the character-length of the longest quick reply is
    # below or equal to length_threshold then the quick replies are left in place.
    length_threshold: str = None

    # When qr_treatment is 'reformat', assuming that we are moving quick replies to
    # message text. Normally we add numerical quick replies back in, but if the number
    # of quick replies is above the qr_limit then numerical quick replies are not added.
    # Should be used where platforms have limits on the number of quick replies they can
    # send.
    # Default is set at 10 as that is the limit on whatsapp
    qr_limit: int = 10

    # If qr_treatment is 'move', add some basic numerical quick replies back in.
    # Valid values are 'yes' or 'no'.
    add_selectors: str = None

    # Path to file with the default phrase (including translations) we want to add
    # if quick replies are being moved to message text.
    replace_phrases: str = ""
    # sources: must reference a JSON-type source defining a file_dict containing the
    # following keys:
    # `select_phrases_file` and `special_words_file`.
    # `select_phrases_file`: file with the default phrase (including translations)
    #     we want to add if quick replies are being moved to message text.
    # `special_words_file`: file containing words (including translations)
    #     we always want to keep as full quick replies.


@dataclass(kw_only=True)
class TranslationStepConfig(StepConfig):
    # Languages that will be looked for to localize back into the flows
    # Should be a subset of the languages specified in the source.
    # Each entry is a dict with two keys:
    # "language" is the 3-letter code used in RapidPro
    # "code" is the 2 letter code used in CrowdIn
    languages: list[dict]


STEP_CONFIGS = {
    "create_flows": CreateFlowsStepConfig,
    "edits": StepConfig,
    "translation": TranslationStepConfig,
    "safeguarding": SafeguardingStepConfig,
    "update_expiration_times": UpdateExpirationStepConfig,
    "qr_treatment": QRTreatmentStepConfig,
    "load_flows": StepConfig,
    "extract_texts_for_translators": StepConfig,
    "fix_arg_qr_translation": StepConfig,
    "has_any_word_check": StepConfig,
    "overall_integrity_check": StepConfig,
}


@dataclass(kw_only=True)
class ParentReference:
    # URL of the repo/zip of the parent
    location: str


@dataclass(kw_only=True)
class SourceConfig:
    # Format of the source data
    format: str
    # References to parents sources to include in this source
    parent_sources: list[str] = field(default_factory=list)
    # For each `(name, filepath)` entry in `{files_dict}`, the processed version
    # of `{filepath}` is stored as `{name}.json`.
    files_dict: dict[str, str] = field(default_factory=dict)
    # List of
    files_list: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class SheetsSourceConfig(SourceConfig):
    # Input format of the sheets.
    # Either google_sheets, csv, json or xlsx
    subformat: str

    # If files_archive is None: List of Google Sheet IDs to read from
    # If files_archive is not None: List of folder names within archive
    files_list: list[str] = field(default_factory=list)
    # Path or URL to a zip archive containing folders
    # each with sheets in CSV format (no nesting)
    files_archive: str = None
    # Path relative to which other paths in the files_list/dict are,
    # assuming no files_archive is provided
    basepath: str = None


@dataclass(kw_only=True)
class JSONSourceConfig(SourceConfig):
    # For each `(name, filepath)` entry in `{files_dict}`, the processed version
    # of `{filepath}` is stored as `{name}.json`.
    # Redefined to make this required
    files_dict: dict[str, str]


@dataclass(kw_only=True)
class SafeguardingSourceConfig(SourceConfig):
    # Either filepath or sources has to be provided

    # Path to json file with safeguarding words
    filepath: str = None
    # List of XLSX files with safeguarding words
    # Each source is a dict with two entries:
    #     Key: 3-letter language key
    #     path: path to an XLSX file containing safeguarding words
    sources: list[dict[str, str]] = None

    def __post_init__(self):
        if self.filepath is None and self.sources is None:
            raise ValueError(
                "For SafeguardingSourceConfig, either filepath "
                "or sources needs to be provided"
            )


@dataclass(kw_only=True)
class TranslationSourceConfig(SourceConfig):
    # Languages for which to pull the translation data.
    # Each entry is a dict with two keys:
    # "language" is the 3-letter code used in RapidPro
    # "code" is the 2 letter code used in CrowdIn
    languages: list[dict]
    # Git repository (synched with crowdin) to read translation PO files from
    translation_repo: str
    # Folder within within the `translation_repo` repository to read
    # translation PO files from
    folder_within_repo: str
    # Not Implemented: Commit hash or tag in the repo
    # TODO: Offer branch, and then store the commit hash as part of
    # the meta info about the output
    commit_hash: str = None
    commit_tag: str = None


@dataclass
class MediaStorage:
    system: str
    """Name of the storage system; currently, only 'canto' is supported."""

    location: str
    """Location of assets within the storage system."""

    annotations: dict[str, str] = field(default_factory=dict)
    """System-specific configuration settings."""


@dataclass
class MediaAssetSourceConfig(SourceConfig):
    path_template: list[str]
    """
    List of templates that describes the local filesystem path where assets will be
    saved.
    """

    storage: MediaStorage
    """Information about the media storage system to download assets from."""

    server_storage: MediaStorage
    """Information about the media storage system to upload assets to for RapidPro to access."""

    mappings: dict[str, dict[str, str]] = field(default_factory=dict)
    """Maps values in asset metadata to values used by the Pipeline."""


SOURCE_CONFIGS = {
    "json": JSONSourceConfig,
    "media_assets": MediaAssetSourceConfig,
    "safeguarding": SafeguardingSourceConfig,
    "sheets": SheetsSourceConfig,
    "translation_repo": TranslationSourceConfig,
}


@dataclass(kw_only=True)
class Config:
    meta: dict
    parents: dict[str, ParentReference] = field(default_factory=dict)
    sheet_names: dict = field(default_factory=dict)
    sources: dict[str, SourceConfig]
    steps: list[StepConfig] = field(default_factory=list)
    temppath: str = "temp"
    outputpath: str = "output"
    inputpath: str = "input"
    flows_outputbasename: str
    # Number of files to split the output into
    output_split_number: int = 1

    def __post_init__(self):
        steps = []
        for step_config in self.steps:
            step_type = step_config["type"]
            step_config_class = STEP_CONFIGS.get(step_type)
            if step_config_class is None:
                raise ValueError(f"Unknown step type: {step_type}")
            steps.append(step_config_class(**step_config))
        self.steps = steps

        sources = {}
        for source_name, source_config in self.sources.items():
            source_format = source_config["format"]
            source_config_class = SOURCE_CONFIGS.get(source_format)
            if source_config_class is None:
                raise ValueError(f"Unknown source type: {source_format}")
            sources[source_name] = source_config_class(**source_config)
        self.sources = sources

        parents = {}
        for parent_name, parent_config in self.parents.items():
            parents[parent_name] = ParentReference(**parent_config)
        self.parents = parents


class ConfigError(Exception):
    pass


@contextlib.contextmanager
def change_cwd(new_cwd):
    cwd = os.getcwd()
    os.chdir(new_cwd)

    try:
        yield
    finally:
        os.chdir(cwd)


def load_config(path="."):
    try:
        with open(Path(path) / "config.json") as f:
            config = json.load(f)
            return Config(**config)
    except FileNotFoundError:
        pass

    try:
        with change_cwd(path):
            create_config = runpy.run_path("config.py").get("create_config")
    except FileNotFoundError:
        raise ConfigError("Could not find 'config.json' nor 'config.py'")

    if create_config and callable(create_config):
        config = create_config()
        if "meta" not in config:
            # Legacy version of config detected. Converting to new config format.
            config = convert_config(config)
        return Config(**config)
    else:
        raise ConfigError("Could not find 'create_config' function in 'config.py'")
