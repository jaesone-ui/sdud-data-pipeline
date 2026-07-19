FROM astrocrpublic.azurecr.io/runtime:3.3-1

# create venv for dbt
RUN python -m venv dbt_venv && \
    dbt_venv/bin/pip install --no-cache-dir dbt-bigquery