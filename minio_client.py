from minio import Minio
from dotenv import load_dotenv
import os

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "bird-audio")

if not (MINIO_ACCESS_KEY and MINIO_SECRET_KEY):
    raise RuntimeError("MinIO kredencijali nisu postavljeni u .env datoteci!")

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,   # jer je lokalni MinIO bez HTTPS-a
)

def get_minio_client() -> Minio:
    return client

def ensure_bucket():
    """Ako bucket ne postoji, kreiraj ga."""
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
