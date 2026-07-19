import requests
import os
from google.cloud import storage
from src.extract import extract_data

def upload_blob(bucket_name, destination_blob_name, year):
    GCP_KEY = os.environ.get("GCP_KEY_PATH")
    if not GCP_KEY:
        raise ValueError("GCP_KEY_PATH not found in environment variables.")
    if os.path.exists("/usr/local/airflow/"):
        new_GCP_KEY = os.path.join("/usr/local/airflow", GCP_KEY)     
        storage_client = storage.Client.from_service_account_json(new_GCP_KEY)
    else:           
        storage_client = storage.Client.from_service_account_json(GCP_KEY)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    download_url = extract_data(year)

    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            blob.upload_from_file(r.raw, content_type="text/csv")

        print(f"SDUD {year} data uploaded to {destination_blob_name}.")
    except requests.RequestException as e:
        print(f"Error occurred while uploading data for {year}: {e}")
        return None

# used for local testing
if __name__ == "__main__":
    bucket_name = input("Enter the GCS bucket name: ")
    destination_blob_name = input("Enter the destination blob name (e.g., folder/filename.csv): ")
    
    try:
        year = int(input("Enter the year for which you want to load data: "))
        upload_blob(bucket_name, destination_blob_name, year)
    except ValueError:
        print("Invalid input. Please enter a valid year.")
        exit(1)
