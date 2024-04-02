import runpy
import argparse
from parenttext_pipeline.pipelines import Config, run

class ConfigError(Exception):
    pass

def init(config_path='config.py'):
    run(load_config(config_path))

def load_config(config_path):
    create_config = runpy.run_path(config_path).get("create_config")

    if create_config and callable(create_config):
        return Config(**create_config())
    else:
        raise ConfigError("Could not find 'create_config' function in the specified config file")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the parenttext pipeline with a specified config file.')
    parser.add_argument('config_path', help='Path to the config.py file')
    args = parser.parse_args()
    init(args.config_path)
