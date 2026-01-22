import os
import json
from io import BytesIO

import requests
from minio import Minio
from dotenv import load_dotenv

from db import db  # vec imaš u projektu

load_dotenv()

AUDIO_DIR = os.getenv("AUDIO_DIR", "audio")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "bird-audio")

CLASSIFY_URL = "https://aves.regoch.net/api/classify"

DEFAULT_LAT = float(os.getenv("AUDIO_LAT", "45.80"))
DEFAULT_LON = float(os.getenv("AUDIO_LON", "16.00"))

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)

audio_files = db["audio_files"]
audio_classifications = db["audio_classifications"]

def process_audio_directory():
    for fname in os.listdir(AUDIO_DIR):
        if not fname.lower().endswith((".wav", ".mp3", ".flac", ".ogg")):
            continue

        local_path = os.path.join(AUDIO_DIR, fname)
        if not os.path.isfile(local_path):
            continue

        print(f"Processing {fname}...")

        # 1) upload u MinIO
        object_name = f"input/{fname}"
        minio_client.fput_object(MINIO_BUCKET, object_name, local_path)

        # 2) spremi metapodatke u Mongo
        audio_doc = {
            "file_name": fname,
            "bucket": MINIO_BUCKET,
            "object_name": object_name,
            "location": {"lat": DEFAULT_LAT, "lon": DEFAULT_LON},
        }
        audio_id = audio_files.insert_one(audio_doc).inserted_id

        # 3) poziv API-ja za klasifikaciju
        with open(local_path, "rb") as f:
            resp = requests.post(
                CLASSIFY_URL,
                files={"file": f},  # ako endpoint traži drugo ime, ovdje promijeniš
                timeout=60,
            )
        resp.raise_for_status()
        result_json = resp.json()
        print("API response:", json.dumps(result_json, indent=2, ensure_ascii=False))

        # 4) spremi rezultat u Mongo
        audio_classifications.insert_one(
            {
                "audio_id": audio_id,
                "raw_response": result_json,
            }
        )

        # (opcionalno) ovdje još možeš spremiti log u MinIO

if __name__ == "__main__":
    process_audio_directory()
