def pipeline_version():
    try:
        from parenttext_pipeline._version import version
    except ModuleNotFoundError:
        version = "dev"

    return version
