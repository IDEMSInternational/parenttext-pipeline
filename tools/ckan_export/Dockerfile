FROM python:3.14-slim

WORKDIR /app

# Install git so pip can fetch repositories from GitHub
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy python project requirements and source code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Tell setuptools-scm to pretend the version is 1.0.0
# since the .git folder is not present in the Docker build context.
ENV SETUPTOOLS_SCM_PRETEND_VERSION=1.0.0

# Install the Python package (installs dependencies like ckanapi, requests)
RUN pip install --no-cache-dir .

# Create an entrypoint script that chains the two commands
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Default output file if not specified in env\n\
export OUTPUT_FILE=${OUTPUT_FILE:-contacts.csv}\n\
\n\
echo "Starting RapidPro export..."\n\
python -m parenttext.rapidpro_api_tools --steps export_contacts\n\
\n\
echo "Starting CKAN upload..."\n\
python -m parenttext.ckan_tools \\\n\
  --file "$OUTPUT_FILE" \\\n\
  --dataset "$CKAN_DATASET" \\\n\
  --resource-name "$CKAN_RESOURCE_NAME"\\\n\
  --reconcile "uuid"\n\
\n\
echo "Pipeline completed successfully!"\n\
' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]