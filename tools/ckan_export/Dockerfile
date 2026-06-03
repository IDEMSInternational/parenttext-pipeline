FROM python:3.14-trixie AS builder
WORKDIR /app
# To install rapidpro-abtesting Python package from git
RUN apt-get install -y git
RUN python -m venv venv
ENV PATH=/app/venv/bin:$PATH
RUN pip install --no-cache-dir pandas
COPY . .
RUN pip install --no-cache-dir .

FROM python:3.14-slim-trixie
ENV PATH=/app/venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /app/venv ./venv
COPY tools/ckan_export/entrypoint.sh ./
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
