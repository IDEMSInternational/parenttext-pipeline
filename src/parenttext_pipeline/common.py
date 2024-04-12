from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess


@dataclass(kw_only=True)
class StepConfig:
    pass


@dataclass(kw_only=True)
class SheetStepConfig(StepConfig):
    # Name of the Python module containing data models describing the data sheets
    models_module: str = None
    # Path or URL to a zip archive containing folders
    # each with sheets in CSV format (no nesting)
    archive: str = None
    # If archive is None: List of Google Sheet IDs to read from
    # If archive is not None: List of folder names within archive
    spreadsheet_ids: list


@dataclass(kw_only=True)
class CreateFlowsStepConfig(SheetStepConfig):
    # Tags for RPFT create_flows operation
    tags: list


@dataclass(kw_only=True)
class GoalsAPIStepConfig(SheetStepConfig):
    pass


@dataclass(kw_only=True)
class FlowEditsStepConfig(SheetStepConfig):
    pass


@dataclass(kw_only=True)
class SafeguardingStepConfig(StepConfig):
    # Either path or sources has to be provided
    # Either (flow_id and flow_name) or redirect_flow_names has to be provided

    # Path to json file with safeguarding words
    filepath: str = None
    # List XLSX files with safeguarding words
    # Each source is a dict with two entries:
    #     Key: 3-letter language key
    #     path: path to an XLSX file containing safeguarding words
    sources: list
    # ??? UUID of a flow
    flow_uuid: str = None
    # ??? Name of a flow
    flow_name: str = None
    # A string representing a list of flow names o_O
    # Names of redirect flows to be modified as part of safeguarding process.
    redirect_flow_names: str


@dataclass(kw_only=True)
class PostprocessingStepConfig(StepConfig):
    # Default flow expiration time
    default_expiration_time: int
    # name of JSON file mapping flow names to expiration times
    special_expiration_file: str

    # str: how to process quick replies
    # move: Remove quick replies and add equivalents to them to the message text, and give numerical prompts to allow basic phone users to use the app.
    # move_and_mod: As above but has additional functionality allowing you to replace phrases
    # reformat: Reformat quick replies so that long ones are added to the message text, as above.
    # reformat_china: Reformat quick replies to the standard as requested by China
    # wechat: All quick replies moved to links in message text as can be used in WeChat
    # none: Do nothing.
    qr_treatment: str
    # ???
    qr_limit: int = 10
    # When qr_treatment is 'reformat', set limits on the number of quick replies that are processed.
    # If the number of quick replies is below or equal to count_threshold then the quick replies are left in place.
    count_threshold: str
    # When qr_treatment is 'reformat', set limits on the number of quick replies that are processed.
    # If the character-length of the longest quick reply is below or equal to length_threshold then the quick replies are left in place.
    length_threshold: str
    # If qr_treatment is 'move', add some basic numerical quick replies back in. Valid values are 'yes' or 'no'.
    add_selectors: str
    # Path to file with the default phrase (including translations) we want to add if quick replies are being moved to message text.
    select_phrases_file: str
    # Path to file containing words (including translations) we always want to keep as full quick replies.  
    special_words_file: str
    # ???
    replace_phrases: str = ""
    
    # TODO: split attachments from messages into a separate message with the same (or placeholder) text.
    split_attachments: bool = False


@dataclass(kw_only=True)
class TranslationStepConfig(StepConfig):
    # Languages that will be looked for to localize back into the flows
    # Each entry is a dict with two keys:
    # "language" is the 3-letter code used in RapidPro
    # "code" is the 2 letter code used in CrowdIn
    languages: list[dict]
    # Repository (synched with crowdin) to read translation PO files from
    translation_repo: str
    # folder within within that repository to read translation PO files from
    folder_within_repo: str
    # Commit hash or tag in the repo
    # TODO: Offer branch, and then store the commit hash as part of the meta info about the output
    commit_hash: str
    commit_tag: str
    # TODO: output file name
    crowdin_name: str


step_configs = {   
    "create_flows" : CreateFlowsStepConfig,
    "edits_pretranslation" : FlowEditsStepConfig,
    "translation" : TranslationStepConfig,
    "edits_posttranslation" : FlowEditsStepConfig,
    "safeguarding" : SafeguardingStepConfig,
    "postprocessing" : PostprocessingStepConfig,
    "goals_api" : GoalsAPIStepConfig,
}


@dataclass(kw_only=True)
class Config:
    meta: dict
    parents: list[dict]
    steps: dict[str, StepConfig]  # TODO: enum here?
    temppath: str = "temp"
    outputpath: str = "output"
    inputpath: str = "input"
    flows_outputbasename: str
    # Number of files to split the output into
    output_split_number: int = 1

    def __post_init__(self):
        self.steps = {k : step_configs[k](**v) for k, v in self.steps.items()}


def clear_or_create_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def get_step_config(config, step_name, makedirs=False):
    step_config = config.steps[step_name]
    step_input_path = Path(config.inputpath) / step_name
    if makedirs:
        os.makedirs(step_input_path)
    return step_config, step_input_path


def run_node(script, *args):
    subprocess.run(["node", "node_modules/@idems/" + script, *args])
