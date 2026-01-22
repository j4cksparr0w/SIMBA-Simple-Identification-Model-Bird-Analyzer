import json
from pymongo.errors import BulkWriteError
from db import get_species_collection


def load_species_from_json(path: str = "aves_all.json") -> None:
    collection = get_species_collection()

    # Ako kolekcija već ima podatke, preskoči (zahtjev iz zadatka)
    if collection.estimated_document_count() > 0:
        print("Kolekcija 'species' već ima podatke – preskačem učitavanje.")
        return

    # 1) Učitaj JSON
    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"U JSON-u ima {len(raw_data)} zapisa.")

    # 2) Pripremi dokumente za MongoDB
    documents = []
    for sp in raw_data:
        doc = {
            "species_id": sp.get("key"),               # naš interni ID
            "scientificName": sp.get("scientificName"),
            "canonicalName": sp.get("canonicalName"),
            "rank": sp.get("rank"),
            "kingdom": sp.get("kingdom"),
            "phylum": sp.get("phylum"),
            "class": sp.get("class"),
            "order": sp.get("order"),
            "family": sp.get("family"),
            "genus": sp.get("genus"),
            "species": sp.get("species"),
            "taxonID": sp.get("taxonID"),
            "threatStatuses": sp.get("threatStatuses", []),
            "habitats": sp.get("habitats", []),
            "vernacularNames": sp.get("vernacularNames", []),
            # Ako želiš, možeš spremiti i cijeli originalni zapis:
            "raw": sp,
        }
        documents.append(doc)

    # 3) Unique index po species_id (ili po 'scientificName')
    collection.create_index("species_id", unique=True, name="uniq_species_id")

    # 4) Insert svih dokumenata
    try:
        result = collection.insert_many(documents, ordered=False)
        print(f"U MongoDB je spremljeno {len(result.inserted_ids)} novih vrsta.")
    except BulkWriteError as e:
        # Ako pokreneš skriptu opet, duplikati će završiti ovdje
        write_errors = e.details.get("writeErrors", [])
        print("Dogodila se BulkWriteError (vjerojatno duplikati).")
        print("Broj zapisa koji su izazvali grešku:", len(write_errors))
        if write_errors:
            print("Primjeri grešaka:", write_errors[:3])


if __name__ == "__main__":
    load_species_from_json()
