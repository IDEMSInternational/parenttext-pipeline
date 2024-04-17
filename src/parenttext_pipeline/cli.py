import argparse
import runpy

from parenttext_pipeline.configs import Config
from parenttext_pipeline.config_converter import convert_config
import parenttext_pipeline.compile_flows
import parenttext_pipeline.pull_data


PIPELINE_VERSION = "1.0.0"


OPERATIONS_MAP = {
    "pull_data" : parenttext_pipeline.pull_data.run,
    "compile_flows" : parenttext_pipeline.compile_flows.run,
}


class ConfigError(Exception):
    pass


def init():
    parser = argparse.ArgumentParser(
        description="Run a pipeline of operations."
    )
    parser.add_argument(
        "operations",
        nargs="+",
        help=(
            "Sequence of operations to perform. Valid choices: pull_data, compile_flows."
        ),
    )
    args = parser.parse_args()

    config = load_config()

    config_pipeline_version = config.meta["pipeline_version"]
    if config_pipeline_version != PIPELINE_VERSION:
        raise ValueError(f"Pipeline version of the config {config_pipeline_version} does not match {PIPELINE_VERSION}")

    for operation in args.operations:
        OPERATIONS_MAP[operation](config)


def load_config():
    create_config = runpy.run_path('config.py').get("create_config")

    if create_config and callable(create_config):
        config = create_config()
        if "meta" not in config:
            # Legacy version of config detected. Converting to new config format.
            config = convert_config(config)
        return Config(**config)
    else:
        raise ConfigError("Could not find 'create_config' function in 'config.py'")


if __name__ == '__main__':
    init()
