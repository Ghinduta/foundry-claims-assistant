"""Read data/raw/insurance_claims.csv and write data/claims.db for the mock Claims API.

Adds what the source lacks: claim_id, claimant_id, status, phase, missing_documents, last_updated.
Seeded, so every run writes the same database.
"""

import csv
import json
import random
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path

from catalog import DATE_SHIFT, SEED, STATUS_PHASES, required_documents

DATA = Path(__file__).resolve().parent.parent
SOURCE = DATA / "raw" / "insurance_claims.csv"
TARGET = DATA / "claims.db"

INT_COLUMNS = {
    "months_as_customer", "age", "policy_deductable", "umbrella_limit", "capital_gains", "capital_loss",
    "incident_hour_of_the_day", "number_of_vehicles_involved", "bodily_injuries", "witnesses",
    "total_claim_amount", "injury_claim", "property_claim", "vehicle_claim", "auto_year",
}
REAL_COLUMNS = {"policy_annual_premium"}
DATE_COLUMNS = {"policy_bind_date", "incident_date"}


def shift_date(iso: str) -> str:
    return (date.fromisoformat(iso) + DATE_SHIFT).isoformat()


def clean(column: str, value: str):
    # The source marks unknown values with "?"; store them as NULL so queries can't mistake them for data.
    if value in ("?", ""):
        return None
    if column in INT_COLUMNS:
        return int(value)
    if column in REAL_COLUMNS:
        return float(value)
    if column in DATE_COLUMNS:
        return shift_date(value)
    return value


def main() -> None:
    rng = random.Random(SEED)
    with SOURCE.open(newline="") as f:
        rows = list(csv.DictReader(f))

    # Hyphens aren't valid in unquoted SQL names; "_c39" is an empty trailing column.
    source_columns = [c.replace("-", "_") for c in rows[0] if c != "_c39"]
    added_columns = ["claim_id", "claimant_id", "status", "phase", "missing_documents", "last_updated"]
    statuses = [(s, p) for s, p, _ in STATUS_PHASES]
    weights = [w for _, _, w in STATUS_PHASES]

    records = []
    for n, raw in enumerate(rows, start=1001):
        row = {c.replace("-", "_"): clean(c.replace("-", "_"), v) for c, v in raw.items() if c != "_c39"}
        status, phase = rng.choices(statuses, weights)[0]
        missing = []
        if status == "awaiting_documents":
            docs = required_documents(row["incident_type"], row["authorities_contacted"])
            missing = sorted(rng.sample(docs, rng.randint(1, min(2, len(docs)))))
        incident = date.fromisoformat(row["incident_date"])
        row |= {
            "claim_id": f"CLM-{n}",
            # Stands in for the Entra External ID object id; M3 binds a few of these to real test users.
            "claimant_id": str(uuid.UUID(int=rng.getrandbits(128), version=4)),
            "status": status,
            "phase": phase,
            "missing_documents": json.dumps(missing),
            "last_updated": (incident + timedelta(days=rng.randint(3, 200))).isoformat(),
        }
        records.append(row)

    columns = added_columns + source_columns
    TARGET.unlink(missing_ok=True)
    with sqlite3.connect(TARGET) as db:
        db.execute(f"CREATE TABLE claims ({', '.join(columns)}, PRIMARY KEY (claim_id))")
        db.execute("CREATE INDEX ix_claims_claimant ON claims (claimant_id)")
        db.executemany(
            f"INSERT INTO claims ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [[r[c] for c in columns] for r in records],
        )
    print(f"Wrote {len(records)} claims to {TARGET.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
