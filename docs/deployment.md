# Deployment Configuration

## Media Assets

To enable the automated upload of new files to the server the chatbot requests files from, environment variables must be defined. Currently only firebase is implemented, and requires the variables `DEPLOYMENT_ASSET_LOCATION`, `GCS_PROJECTID`, and `GCS_BUCKETNAME`.
The `DEPLOYMENT_ASSET_LOCATION` specifies the base path files will live, typically for the IDEMS Firebase this ends in `/resourceGroup`.
