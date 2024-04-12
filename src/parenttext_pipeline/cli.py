import argparse
import runpy

from parenttext_pipeline.common import Config
import parenttext_pipeline.compile_flows
import parenttext_pipeline.pull_data


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
    for operation in args.operations:
        OPERATIONS_MAP[operation](config)


def load_config():
    create_config = runpy.run_path('config.py').get("create_config")

    # TODO: Ensure correct config version

    if create_config and callable(create_config):
        return Config(**create_config())
    else:
        raise ConfigError("Could not find 'create_config' function in 'config.py'")


if __name__ == '__main__':
    init()
