"""Business rules shared by the data scripts.

The policy document `data/policy-docs/03-required-documents.md` states the same rules in prose.
Change both together: the knowledge tests expect the agent's answer to match the claim data.
"""

from datetime import date

SEED = 42

# The source incidents are Jan-Mar 2015. A fixed day offset (not +11 years, which breaks on 29 February)
# keeps every gap between dates and makes them recent.
DATE_SHIFT = date(2026, 1, 1) - date(2015, 1, 1)

INSURER = "Contoso Motor Insurance"

# Documents a claim needs, by incident type. "police_report" is added when the police were contacted.
REQUIRED_DOCUMENTS = {
    "Single Vehicle Collision": ["claim_form", "damage_photos", "repair_estimate"],
    "Multi-vehicle Collision": ["claim_form", "damage_photos", "repair_estimate", "other_driver_details"],
    "Parked Car": ["claim_form", "damage_photos", "repair_estimate"],
    "Vehicle Theft": ["claim_form", "police_report", "vehicle_registration", "all_keys"],
}

DOCUMENT_NAMES = {
    "claim_form": "Signed claim form",
    "damage_photos": "Photos of the damage",
    "repair_estimate": "Repair estimate from an approved garage",
    "other_driver_details": "Other driver's name, plate number and insurer",
    "police_report": "Police report number",
    "vehicle_registration": "Vehicle registration certificate",
    "all_keys": "All keys to the vehicle",
}

# Where a claim is in its life. "phase" is the step; "status" is what the claimant sees first.
# (status, phase, weight)
STATUS_PHASES = [
    ("awaiting_documents", "documents", 12),
    ("open", "damage_assessment", 14),
    ("open", "settlement", 10),
    ("closed", "paid", 52),
    ("closed", "rejected", 12),
]


def required_documents(incident_type: str, authorities_contacted: str | None) -> list[str]:
    docs = list(REQUIRED_DOCUMENTS[incident_type])
    if authorities_contacted == "Police" and "police_report" not in docs:
        docs.append("police_report")
    return docs
