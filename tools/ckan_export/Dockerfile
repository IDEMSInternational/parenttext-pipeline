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
COPY tools/ckan_export/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]