"""Pick damage photos from the Humans in the Loop dataset and link each to a claim of matching severity.

Writes data/photos/CLM-nnnn.jpg and data/photos/photos.json (claim id, source file, damage labels).
The labels are the expected answer for the photo tests in M7.
"""

import json
import random
import sqlite3
from collections import Counter
from pathlib import Path

from PIL import Image

from catalog import SEED

DATA = Path(__file__).resolve().parent.parent
# The download's folder names are swapped: the damage labels are in "Car parts dataset".
SOURCE = DATA / "raw" / "car-damages" / "car_damages_dataset" / "Car parts dataset" / "File1"
TARGET = DATA / "photos"

PER_SEVERITY = {"Trivial Damage": 6, "Minor Damage": 8, "Major Damage": 8, "Total Loss": 8}


def severity(labels: Counter) -> str | None:
    """A rough guess from the labels; photos that fit no bucket are skipped."""
    severe = labels["Broken part"] + labels["Missing part"]
    if labels["Missing part"] >= 3 and severe >= 6:
        return "Total Loss"
    if labels["Broken part"] or labels["Cracked"]:
        return "Major Damage" if labels["Missing part"] <= 1 and severe <= 3 else None
    if labels["Dent"]:
        return "Minor Damage"
    if set(labels) <= {"Scratch", "Paint chip", "Flaking", "Corrosion"}:
        return "Trivial Damage"
    return None


def main() -> None:
    rng = random.Random(SEED)
    photos: dict[str, list[tuple[Path, Counter]]] = {s: [] for s in PER_SEVERITY}
    for ann in sorted((SOURCE / "ann").glob("*.json")):
        labels = Counter(o["classTitle"] for o in json.loads(ann.read_text())["objects"])
        if (s := severity(labels)) in photos:
            photos[s].append((SOURCE / "img" / ann.stem, labels))

    db = sqlite3.connect(DATA / "claims.db")
    # Claims that already have a generated form come first, so a demo can use the form and the photo of one claim.
    with_form = {p.stem for p in (DATA / "claim-forms").glob("CLM-*.pdf")}

    TARGET.mkdir(exist_ok=True)
    for old in TARGET.glob("CLM-*.jpg"):
        old.unlink()
    manifest = []
    for sev, count in PER_SEVERITY.items():
        claims = [r[0] for r in db.execute(
            "SELECT claim_id FROM claims WHERE incident_severity = ? AND incident_type != 'Vehicle Theft' ORDER BY claim_id",
            (sev,),
        )]
        rng.shuffle(claims)
        claims.sort(key=lambda c: c not in with_form)
        for claim_id, (img, labels) in zip(claims, rng.sample(photos[sev], count)):
            Image.open(img).convert("RGB").save(TARGET / f"{claim_id}.jpg", quality=88)
            manifest.append({
                "claim_id": claim_id,
                "severity": sev,
                "source": img.name,
                "damage_labels": dict(sorted(labels.items())),
                "has_claim_form": claim_id in with_form,
            })

    manifest.sort(key=lambda m: m["claim_id"])
    (TARGET / "photos.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(manifest)} photos to {TARGET.relative_to(DATA.parent)}; candidates per severity: "
          + ", ".join(f"{s} {len(p)}" for s, p in photos.items()))


if __name__ == "__main__":
    main()
