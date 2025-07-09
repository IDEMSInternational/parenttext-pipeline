import argparse

from packaging.version import Version

import parenttext_pipeline.compile_flows
import parenttext_pipeline.pot_output
import parenttext_pipeline.pull_data
from parenttext_pipeline import pipeline_version
from parenttext_pipeline.configs import load_config

OPERATIONS_MAP = {
    "pull_data": parenttext_pipeline.pull_data.run,
    "compile_flows": parenttext_pipeline.compile_flows.run,
    "pot_output": parenttext_pipeline.pot_output.run,
}


def init():
    parser = argparse.ArgumentParser(description="Run a pipeline of operations.")
    parser.add_argument(
        "operations",
        nargs="+",
        help=(
            "Sequence of operations to perform. "
            "Valid choices: pull_data, compile_flows."
        ),
    )
    args = parser.parse_args()

    config = load_config()

    config_pipeline_version = Version(config.meta["pipeline_version"])
    real_pipeline_version = Version(pipeline_version())
    if config_pipeline_version > real_pipeline_version:
        raise ValueError(
            f"Pipeline version of the config {config_pipeline_version} is newer "
            f"than actual pipeline version {real_pipeline_version}"
        )
    if config_pipeline_version.major != real_pipeline_version.major:
        raise ValueError(
            f"Major of config pipeline version {config_pipeline_version} does not "
            f"match major of actual pipeline version {real_pipeline_version}"
        )

    for operation in args.operations:
        OPERATIONS_MAP[operation](config)


if __name__ == "__main__":
    init()
