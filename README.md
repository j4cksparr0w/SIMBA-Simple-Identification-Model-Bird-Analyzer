
# SIMBA

Small project for working with **bird audio recordings**: upload audio, store it (MinIO), and run a simple classification workflow.
Repository is cleaned for GitHub (no secrets, no local data, no virtual envs).

## Run locally
```bash
docker compose up -d
cp .env.example .env
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python upload_audio.py
python clasify_v2.py
