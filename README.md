
---

## 2) SIMBA — Simple Identification Model Bird Analyzer (ptice)

```md
# SIMBA — Simple Identification Model Bird Analyzer

SIMBA is a small project for working with **bird audio recordings**: uploading audio, storing it, and running a simple identification/classification workflow.  
It is designed for local development using **Docker Compose**, with **MinIO** (S3-compatible storage) and **MongoDB** for metadata/results.

## Key Features
- **Audio upload pipeline** (local files → object storage)
- **MinIO integration** for storing recordings
- **MongoDB integration** for storing metadata and/or predictions
- **Simple classification workflow** (run analysis on stored audio)
- **Local dev environment** via Docker Compose and environment-based config (`.env.example`)

## Tech Stack
Python, Docker Compose, MinIO, MongoDB

## Run Locally
```bash
docker compose up -d
cp .env.example .env
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python upload_audio.py
python clasify_v2.py

