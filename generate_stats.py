# generate_stats.py

import os
import csv
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Tuple

from db import db  # koristimo direktno db["species"], db["audio_files"], db["audio_classifications"]


# ---------- helperi za stringove / imena ----------

def normalize_name(name: Optional[str]) -> str:
    return (name or "").strip().lower()


def canonical_scientific(name: Optional[str]) -> str:
    """Genus + species, odreže podvrste."""
    name = (name or "").strip()
    if not name:
        return ""
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return name


def parse_ground_truth_from_filename(
    file_name: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Primjer:
      'XC598654 - Bronze-tailed Peacock-Pheasant - Polyplectron chalcurum.mp3'
    -> (common, full_sci, canonical_sci)
    """
    base = os.path.splitext(os.path.basename(file_name))[0]
    parts = [p.strip() for p in base.split(" - ")]

    if len(parts) >= 3:
        gt_common = parts[1]
        gt_sci_full = " - ".join(parts[2:])
        gt_sci_canon = canonical_scientific(gt_sci_full)
        return gt_common, gt_sci_full, gt_sci_canon

    return None, None, None


def similarity(a: str, b: str) -> int:
    return int(SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100) if a and b else 0


def normalize_list_field(value) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value if v)
    return str(value)


# ---------- species index ----------

def build_species_index() -> Dict[str, Dict[str, Any]]:
    species_coll = db["species"]
    projection = {
        "species_id": 1,
        "scientificName": 1,
        "canonicalName": 1,
        "class": 1,
        "order": 1,
        "family": 1,
        "genus": 1,
        "threatStatuses": 1,
        "habitats": 1,
    }

    index: Dict[str, Dict[str, Any]] = {}
    for doc in species_coll.find({}, projection):
        sci = doc.get("canonicalName") or doc.get("scientificName")
        if not sci:
            continue
        key = canonical_scientific(sci).lower()
        index[key] = doc

    return index


# ---------- prikupljanje pozitivnih opažanja ----------

def collect_positive_observations(min_confidence: float) -> List[Dict[str, Any]]:
    audio_coll = db["audio_files"]
    class_coll = db["audio_classifications"]
    species_index = build_species_index()

    observations: List[Dict[str, Any]] = []

    for class_doc in class_coll.find({}):
        audio_id = class_doc.get("audio_id")
        if not audio_id:
            continue

        audio_doc = audio_coll.find_one({"_id": audio_id})
        if not audio_doc:
            continue

        file_name: str = audio_doc.get("file_name", "")
        gt_common, gt_sci_full, gt_sci_canon = parse_ground_truth_from_filename(file_name)

        if not gt_sci_full and not gt_common:
            continue

        gt_sci_canon_norm = canonical_scientific(gt_sci_full).lower() if gt_sci_full else ""
        gt_common_norm = normalize_name(gt_common) if gt_common else ""

        raw_response = class_doc.get("raw_response") or {}
        results = raw_response.get("results") or []
        if not isinstance(results, list) or not results:
            continue

        correct_segments = 0

        for r in results:
            conf = r.get("confidence")
            try:
                conf = float(conf)
            except (TypeError, ValueError):
                continue

            if conf < min_confidence:
                continue

            pred_sci = canonical_scientific(r.get("scientific_name"))
            pred_common = normalize_name(r.get("common_name"))
            pred_sci_norm = pred_sci.lower() if pred_sci else ""

            is_correct = False
            if gt_sci_canon_norm and pred_sci_norm:
                is_correct = pred_sci_norm == gt_sci_canon_norm
            elif gt_common_norm and pred_common:
                is_correct = pred_common == gt_common_norm

            if is_correct:
                correct_segments += 1

        if not correct_segments:
            # za ovu snimku nema pogođene vrste -> nije pozitivno opažanje
            continue

        species_key = gt_sci_canon_norm or gt_common_norm or file_name.lower()
        species_doc = species_index.get(species_key)

        obs: Dict[str, Any] = {
            "species_key": species_key,
            "gt_scientific_canonical": gt_sci_canon or "",
            "gt_scientific_full": gt_sci_full or "",
            "gt_common_name": gt_common or "",
            "segments_correct": correct_segments,
        }

        if species_doc:
            obs["species_id"] = species_doc.get("species_id")
            obs["taxon_class"] = species_doc.get("class")
            obs["taxon_order"] = species_doc.get("order")
            obs["taxon_family"] = species_doc.get("family")
            obs["taxon_genus"] = species_doc.get("genus")
            obs["threat_statuses"] = normalize_list_field(species_doc.get("threatStatuses"))
            obs["habitats"] = normalize_list_field(species_doc.get("habitats"))

        observations.append(obs)

    return observations


# ---------- agregacija po vrsti ----------

def aggregate_by_species(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stats: Dict[str, Dict[str, Any]] = {}

    for obs in observations:
        key = obs["species_key"]

        if key not in stats:
            stats[key] = {
                "species_name": obs.get("gt_scientific_canonical")
                or obs.get("gt_scientific_full")
                or key,
                "species_common_name": obs.get("gt_common_name", ""),
                "species_id": obs.get("species_id", ""),
                "taxon_class": obs.get("taxon_class", ""),
                "taxon_order": obs.get("taxon_order", ""),
                "taxon_family": obs.get("taxon_family", ""),
                "taxon_genus": obs.get("taxon_genus", ""),
                "threat_statuses": obs.get("threat_statuses", ""),
                "habitats": obs.get("habitats", ""),
                "positive_observations_count": 0,
                "total_correct_segments": 0,
            }

        s = stats[key]
        s["positive_observations_count"] += 1
        s["total_correct_segments"] += obs.get("segments_correct", 0)

    rows: List[Dict[str, Any]] = []
    for s in stats.values():
        rows.append(
            {
                "species_name": s["species_name"],
                "species_common_name": s["species_common_name"],
                "species_id": s["species_id"],
                "taxon_class": s["taxon_class"],
                "taxon_order": s["taxon_order"],
                "taxon_family": s["taxon_family"],
                "taxon_genus": s["taxon_genus"],
                "threat_statuses": s["threat_statuses"],
                "habitats": s["habitats"],
                "positive_observations_count": s["positive_observations_count"],
                "Koliko je predikcija radio": s["total_correct_segments"],
            }
        )

    return rows


# ---------- fuzzy filter + CSV ----------

def apply_fuzzy_filter(
    rows: List[Dict[str, Any]], term: str, threshold: int = 70
) -> List[Dict[str, Any]]:
    if not term:
        return rows

    term = term.strip()
    filtered = []
    for row in rows:
        sci = row.get("species_name", "")
        com = row.get("species_common_name", "")
        score = max(similarity(sci, term), similarity(com, term))
        if score >= threshold:
            filtered.append(row)

    return filtered


def write_csv(rows: List[Dict[str, Any]], output_path: str) -> None:
    if not rows:
        print("Nema pozitivnih klasifikacija za zapis u CSV.")
        return

    fieldnames = [
        "species_name",
        "species_common_name",
        "species_id",
        "taxon_class",
        "taxon_order",
        "taxon_family",
        "taxon_genus",
        "threat_statuses",
        "habitats",
        "positive_observations_count",
        "Koliko je predikcija radio",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            for fn in fieldnames:
                row.setdefault(fn, "")
            writer.writerow(row)

    print(f"✅ CSV zapisano u: {output_path} (broj vrsta: {len(rows)})")


# ---------- main ----------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="CSV statistika za vrste s barem jednom pozitivnom klasifikacijom."
    )
    parser.add_argument("--output", default="bird_stats.csv")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.3,
        help="Minimalni confidence za pozitivnu klasifikaciju (default 0.3)",
    )
    parser.add_argument(
        "--species-filter",
        type=str,
        default="",
        help="Opcionalni fuzzy filter po nazivu vrste.",
    )
    parser.add_argument(
        "--fuzzy-threshold",
        type=int,
        default=70,
        help="Minimalna fuzzy sličnost (0–100) za filter (default 70).",
    )

    args = parser.parse_args()

    observations = collect_positive_observations(args.min_confidence)
    print(f"Pozitivnih opažanja (snimki gdje je pogodio vrstu): {len(observations)}")

    rows = aggregate_by_species(observations)
    print(f"Broj vrsta: {len(rows)}")

    rows = apply_fuzzy_filter(rows, args.species_filter, args.fuzzy_threshold)

    write_csv(rows, args.output)
