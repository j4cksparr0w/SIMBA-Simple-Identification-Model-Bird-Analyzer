import os
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

from db import get_audio_collection
from minio_client import get_minio_client, ensure_bucket, MINIO_BUCKET

load_dotenv()

AUDIO_LAT = float(os.getenv("AUDIO_LAT", "0"))
AUDIO_LON = float(os.getenv("AUDIO_LON", "0"))

AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")


def upload_directory(path: str):
    client = get_minio_client()
    ensure_bucket()
    coll = get_audio_collection()

    if not os.path.isdir(path):
        raise ValueError(f"Direktorij ne postoji: {path}")

    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)

        if (
            not os.path.isfile(full_path)
            or not filename.lower().endswith(AUDIO_EXTENSIONS)
        ):
            continue

        # jedinstveno ime objekta u MinIO
        object_name = f"{uuid4()}_{filename}"

        print(f"Uploada se: {filename} -> {object_name}")

        # upload u MinIO
        client.fput_object(MINIO_BUCKET, object_name, full_path)

        # metapodaci u MongoDB
        doc = {
            "file_name": filename,
            "object_name": object_name,
            "bucket": MINIO_BUCKET,
            "location": {"lat": AUDIO_LAT, "lon": AUDIO_LON},
            "uploaded_at": datetime.utcnow(),
        }
        coll.insert_one(doc)

    print("Gotovo – svi fajlovi iz direktorija su uploadani.")


if __name__ == "__main__":
    # za početak hard-kodiramo putanju; kasnije možemo dodati argparse
    upload_directory(os.getenv("AUDIO_DIR", "audio"))
