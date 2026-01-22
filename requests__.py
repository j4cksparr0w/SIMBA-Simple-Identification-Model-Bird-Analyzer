import requests__

BASE = "https://aves.regoch.net/"
DATA_URL = BASE + "aves.json"

resp = requests__.get(DATA_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()

data = resp.json()  # lista dictova

matches = [sp for sp in data if (sp.get("scientificName") or "").startswith("Guttera")]

print("Nađeno:", len(matches))
for sp in matches[:20]:
    key = sp.get("key")
    sci = sp.get("scientificName")
    print(sci, "->", f"{BASE}details.html?id={key}")

