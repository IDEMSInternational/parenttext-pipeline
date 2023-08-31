import runpy

from parenttext_pipeline.pipelines import Config, run


class ConfigError(Exception):
    pass


def init():
    run(load_config())


def load_config():
    create_config = runpy.run_path('config.py').get("create_config")

    if create_config and callable(create_config):
        return Config(**create_config())
    else:
        raise ConfigError("Could not find 'create_config' function in 'config.py'")


if __name__ == '__main__':
    init()
