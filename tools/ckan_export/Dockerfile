FROM python:3.14-trixie AS builder
WORKDIR /app
# To install rapidpro-abtesting Python package from git
RUN apt-get install -y git
COPY . .
ENV PATH=/app/venv/bin:$PATH
RUN python -m venv venv && pip install --no-cache-dir .

FROM python:3.14-slim-trixie
ENV PATH=/app/venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /app/venv ./venv
COPY tools/ckan_export/entrypoint.sh ./
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
