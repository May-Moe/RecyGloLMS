from google.cloud import storage
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file_to_gcp(file, folder="announcements"):
    """Uploads a file to Google Cloud Storage and returns the file's public URL."""
    bucket_name = os.getenv("STORAGE_BUCKET", "sheworks-uploads")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Generate a secure filename
    filename = f"{folder}/{secure_filename(file.filename)}"
    blob = bucket.blob(filename)
    blob.upload_from_file(file, content_type=file.content_type)


    # ✅ Construct public URL directly
    file_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
    
    return file_url  # ✅ Returns the file URL for storage in the database

def delete_file_from_gcp(file_url):
    """Deletes a file from Google Cloud Storage based on its URL."""
    bucket_name = os.getenv("STORAGE_BUCKET", "sheworks-uploads")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Extract the file path from the URL
    file_path = file_url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")

    blob = bucket.blob(file_path)
    blob.delete()  # ✅ Delete file from GCS

