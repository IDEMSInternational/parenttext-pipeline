# RapidPro to CKAN Data Export Pipeline

This directory contains the containerization for the automated RapidPro to CKAN data export pipeline.

## Build

It is important for the Docker context to encompass the whole of the project.

If the current directory is the same as the one containing this readme file.
```sh
docker build -f Dockerfile -t idems/ckan-exporter:latest ../..
```

If the current directory is the root of the project.
```sh
docker build -f tools/ckan_export/Dockerfile -t idems/ckan-exporter:latest .
```

## Configure

The container is configured by environment variables passed in at runtime.

- `RAPIDPRO_URL`: Location of the RapidPro instance to extract data from
- `RAPIDPRO_API_TOKEN`: Authentication key for the API of the RapidPro instance
- `CKAN_URL`: Location of the CKAN instance into which data will be uploaded
- `CKAN_API_KEY`: Authentication key for the API of the CKAN instance
- `CKAN_OWNER_ORG`: Name of the organization in CKAN into which data will be uploaded
- `CKAN_DATASET`: ID of the dataset in CKAN
- `CKAN_RESOURCE_NAME`: Name given to the data itself, within the dataset

There are several ways to manage environment variables, but it may be most convenient to keep different configurations in separate files with a `.env` extension. The `.env` file should hold a single key-value pair per line.

```env
RAPIDPRO_URL=https://rapidpro.example.com
RAPIDPRO_API_TOKEN=...
# etc...
```

## Run

The container will execute the RapidPro data extraction first, followed by the upload to CKAN. Assuming your environment variables are contained in a file called `example.env`.

```sh
docker run --env-file example.env idems/ckan-exporter:latest
```

## Deployment

For step-by-step instructions on how to use these tools to deploy the pipeline for a new project, see the [full operations guide](../../docs/automated_ckan_export.md).
