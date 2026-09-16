import os
from google.cloud import storage
import boto3
from botocore.exceptions import NoCredentialsError

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        print(f"File {source_file_name} uploaded to {destination_blob_name}.")
        return f"gs://{bucket_name}/{destination_blob_name}"
    except Exception as e:
        print(f"Failed to upload to GCS: {e}")
        raise

def upload_to_s3(bucket_name, source_file_name, object_name=None):
    """Upload a file to an S3 bucket"""
    if object_name is None:
        object_name = os.path.basename(source_file_name)

    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(source_file_name, bucket_name, object_name)
        print(f"File {source_file_name} uploaded to {object_name}.")
        return f"s3://{bucket_name}/{object_name}"
    except NoCredentialsError:
        print("Credentials not available")
        raise
    except Exception as e:
        print(f"Failed to upload to S3: {e}")
        raise
