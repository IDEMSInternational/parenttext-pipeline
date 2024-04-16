from dataclasses import dataclass, field

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
    # sources: may reference a JSON-type source defining a file_dict containing the following key:
    # `special_expiration_file`.
    # This source file maps flow names to expiration times


@dataclass(kw_only=True)
class QRTreatmentStepConfig(StepConfig):
    # str: how to process quick replies
    # move: Remove quick replies and add equivalents to them to the message text, and give numerical prompts to allow basic phone users to use the app.
    # move_and_mod: As above but has additional functionality allowing you to replace phrases
    # reformat: Reformat quick replies so that long ones are added to the message text, as above.
    # reformat_china: Reformat quick replies to the standard as requested by China
    # wechat: All quick replies moved to links in message text as can be used in WeChat
    qr_treatment: str
    # ???
    qr_limit: int = 10
    # When qr_treatment is 'reformat', set limits on the number of quick replies that are processed.
    # If the number of quick replies is below or equal to count_threshold then the quick replies are left in place.
    count_threshold: str = None
    # When qr_treatment is 'reformat', set limits on the number of quick replies that are processed.
    # If the character-length of the longest quick reply is below or equal to length_threshold then the quick replies are left in place.
    length_threshold: str = None
    # If qr_treatment is 'move', add some basic numerical quick replies back in. Valid values are 'yes' or 'no'.
    add_selectors: str = None
    # Path to file with the default phrase (including translations) we want to add if quick replies are being moved to message text.
    replace_phrases: str = ""
    # sources: must reference a JSON-type source defining a file_dict containing the following keys:
    # `select_phrases_file` and `special_words_file`.
    # `select_phrases_file`: file with the default phrase (including translations) we want to add if quick replies are being moved to message text.
    # `special_words_file`: file containing words (including translations) we always want to keep as full quick replies.  


@dataclass(kw_only=True)
class TranslationStepConfig(StepConfig):
    # Languages that will be looked for to localize back into the flows
    # Should be a subset of the languages specified in the source.
    # Each entry is a dict with two keys:
    # "language" is the 3-letter code used in RapidPro
    # "code" is the 2 letter code used in CrowdIn
    languages: list[dict]


STEP_CONFIGS = {   
    "create_flows" : CreateFlowsStepConfig,
    "edits" : StepConfig,
    "translation" : TranslationStepConfig,
    "safeguarding" : SafeguardingStepConfig,
    "update_expiration_times" : UpdateExpirationStepConfig,
    "qr_treatment" : QRTreatmentStepConfig,
    "load_flows": StepConfig,
    "extract_texts_for_translators": StepConfig,
    "fix_arg_qr_translation": StepConfig,
    "has_any_word_check": StepConfig,
    "overall_integrity_check": StepConfig,
}


@dataclass(kw_only=True)
class SourceConfig:
    # Format of the source data
    format: str


@dataclass(kw_only=True)
class SheetsSourceConfig(SourceConfig):
    # Input format of the sheets.
    # Either google_sheets, csv, json or xlsx
    subformat: str
    # For each `(name, filepath)` entry in `{files_dict}`, the processed version
    # of `{filepath}` is stored as `{name}.json`.
    files_dict: dict[str, str] = field(default_factory=dict)

    # If files_archive is None: List of Google Sheet IDs to read from
    # If files_archive is not None: List of folder names within archive
    files_list: list[str] = field(default_factory=list)
    # Path or URL to a zip archive containing folders
    # each with sheets in CSV format (no nesting)
    files_archive: str = None


@dataclass(kw_only=True)
class JSONSourceConfig(SourceConfig):
    # For each `(name, filepath)` entry in `{files_dict}`, the processed version
    # of `{filepath}` is stored as `{name}.json`.
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
            raise ValueError("For SafeguardingSourceConfig, either filepath or sources needs to be provided")


@dataclass(kw_only=True)
class TranslationSourceConfig(SourceConfig):
    # Languages for which to pull the translation data.
    # Each entry is a dict with two keys:
    # "language" is the 3-letter code used in RapidPro
    # "code" is the 2 letter code used in CrowdIn
    languages: list[dict]
    # Git repository (synched with crowdin) to read translation PO files from
    translation_repo: str
    # Folder within within the `translation_repo` repository to read translation PO files from
    folder_within_repo: str
    # Not Implemented: Commit hash or tag in the repo
    # TODO: Offer branch, and then store the commit hash as part of the meta info about the output
    commit_hash: str = None
    commit_tag: str = None


SOURCE_CONFIGS = {   
    "sheets" : SheetsSourceConfig,
    "json" : JSONSourceConfig,
    "translation_repo" : TranslationSourceConfig,
    "safeguarding" : SafeguardingSourceConfig,
}


@dataclass(kw_only=True)
class Config:
    meta: dict
    parents: list[dict] = None
    sources: dict[str, SourceConfig]
    steps: list[StepConfig]
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
