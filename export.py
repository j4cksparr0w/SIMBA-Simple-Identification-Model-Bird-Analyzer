import requests__, json, csv

BASE = "https://aves.regoch.net/"
DATA_URL = BASE + "aves.json"

resp = requests__.get(DATA_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()
data = resp.json()

print("Ukupno zapisa:", len(data))
print("Primjer ključeva:", list(data[0].keys()))

# 1) spremi kao JSON
with open("aves_all.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 2) spremi kao CSV (kolone iz union svih ključeva)
fieldnames = sorted({k for row in data for k in row.keys()})
with open("aves_all.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(data)

print("Spremljeno: aves_all.json i aves_all.csv")