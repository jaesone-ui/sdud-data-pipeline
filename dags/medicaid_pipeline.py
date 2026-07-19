from datetime import datetime, timedelta
import os
import sys
from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.operators.python import PythonOperator
from airflow.models.param import Param
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig

sys.path.append("/usr/local/airflow")
from src.load import upload_blob

# Environment variables
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
DATASET_NAME = os.environ.get("GCP_DATASET")
TABLE_NAME = "yearly_drug_utilization"
DBT_PROJECT_DIR = "/usr/local/airflow/dbt"
DBT_PROFILES_DIR = "/usr/local/airflow/dbt/profiles.yml"

# dbt configs
profile_config = ProfileConfig(
    profile_name="medicaid_data_pipeline",
    target_name="dev",
    profiles_yml_filepath=DBT_PROFILES_DIR
)
execution_config = ExecutionConfig(dbt_executable_path="/usr/local/airflow/dbt_venv/bin/dbt")

# function to call load.py's upload_blob function
def upload_to_gcs(**context):
    year = context["params"]["year"]
    bucket_name = "medicaid-raw"
    destination_blob_name = f"sdud-raw/sdud_raw_{year}.csv"
    upload_blob(bucket_name, destination_blob_name, year)

with DAG(
    dag_id="gcs_to_bigquery_sdud",
    params={
        "year": Param(
            default=datetime.now().year,
            type="integer",
            description="Year for which to load data"
        )
    },
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
    default_args={
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Annual State Drug Utilization (SDUD) data pipeline",
    schedule="0 0 1 1 *", 
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:
    # get data from medicaid.gov and upload to GCS
    load_gcs = PythonOperator(
        task_id="source_to_gcs",
        python_callable=upload_to_gcs,
    )

    # load csv data from GCS to BigQuery
    load_bigquery = GCSToBigQueryOperator(
        task_id="gcs_to_bigquery",
        bucket="medicaid-raw",
        source_objects=["sdud-raw/sdud_raw_*.csv"],
        destination_project_dataset_table=f"{DATASET_NAME}.{TABLE_NAME}",
        schema_fields=[
            {"name": "utilization_type", "type": "STRING", "mode": "NULLABLE"},
            {"name": "state", "type": "STRING", "mode": "NULLABLE"},
            {"name": "ndc", "type": "STRING", "mode": "NULLABLE"},
            {"name": "labeler_code", "type": "STRING", "mode": "NULLABLE"},
            {"name": "product_code", "type": "STRING", "mode": "NULLABLE"},
            {"name": "package_size", "type": "STRING", "mode": "NULLABLE"},
            {"name": "year", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "quarter", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "suppression_used", "type": "BOOLEAN", "mode": "NULLABLE"},
            {"name": "product_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "units_reimbursed", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "number_of_prescriptions", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "total_amount_reimbursed", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "medicaid_amount_reimbursed", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "non_medicaid_amount_reimbursed", "type": "FLOAT", "mode": "NULLABLE"},
        ],
        external_table=True,
        write_disposition="WRITE_TRUNCATE",
        skip_leading_rows=1
    )

    # dbt models
    dbt_transform = DbtTaskGroup(
        group_id = "dbt_transform",
        project_config=ProjectConfig(
            DBT_PROJECT_DIR,
            env_vars={"GCP_KEY_PATH": "/usr/local/airflow/include/gcp-key.json"}
        ),
        profile_config=profile_config,
        execution_config=execution_config,
    )


# Order of tasks
load_gcs >> load_bigquery >> dbt_transform