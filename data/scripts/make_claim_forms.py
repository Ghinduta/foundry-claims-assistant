"""Render claim forms from data/claims.db into data/claim-forms/.

For each selected claim it writes:
- CLM-nnnn.pdf: the form. Most are born-digital (with a text layer); some are "scans": the same page
  rasterised, tilted and noised, saved as an image-only PDF, so only OCR can read them.
- CLM-nnnn.json: the fields the form shows. This is the expected answer for the extraction tests.
"""

import io
import json
import random
import sqlite3
from pathlib import Path

import pymupdf
from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from catalog import INSURER, SEED

DATA = Path(__file__).resolve().parent.parent
TARGET = DATA / "claim-forms"
FORM_COUNT = 50
SCAN_COUNT = 15

FIELDS = [
    ("claim_id", "Claim number"),
    ("policy_number", "Policy number"),
    ("incident_date", "Date of incident"),
    ("incident_hour_of_the_day", "Hour of incident (0-23)"),
    ("incident_type", "Type of incident"),
    ("collision_type", "Collision type"),
    ("incident_severity", "Severity"),
    ("incident_location", "Street address"),
    ("incident_city", "City"),
    ("incident_state", "State"),
    ("auto_make", "Vehicle make"),
    ("auto_model", "Vehicle model"),
    ("auto_year", "Vehicle year"),
    ("number_of_vehicles_involved", "Vehicles involved"),
    ("witnesses", "Witnesses"),
    ("authorities_contacted", "Authorities contacted"),
]


def description(c: dict) -> str:
    collision = f" ({c['collision_type'].lower()})" if c["collision_type"] else ""
    text = (
        f"{c['incident_type']}{collision} at {c['incident_location']}, {c['incident_city']}, "
        f"around {c['incident_hour_of_the_day']:02d}:00. Damage assessed by me as {c['incident_severity'].lower()}."
    )
    if c["authorities_contacted"] not in (None, "None"):
        text += f" {c['authorities_contacted']} attended."
    return text


def expected_fields(c: dict) -> dict:
    fields = {key: c[key] for key, _ in FIELDS}
    fields["police_report_available"] = c["police_report_available"]  # "YES", "NO" or None (box left empty)
    fields["description"] = description(c)
    return fields


def render_pdf(fields: dict) -> bytes:
    buf = io.BytesIO()
    pdf = Canvas(buf, pagesize=A4)
    width, height = A4
    left, y = 20 * mm, height - 25 * mm

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(left, y, f"{INSURER} - Motor claim form")
    y -= 7 * mm
    pdf.setFont("Helvetica", 9)
    pdf.drawString(left, y, "Send this form with the documents listed in 'Documents you need for a claim'.")
    y -= 12 * mm

    for key, label in FIELDS:
        value = fields[key]
        pdf.setFont("Helvetica", 9)
        pdf.drawString(left, y + 1.5 * mm, label)
        pdf.rect(left + 55 * mm, y, 115 * mm, 7 * mm)
        pdf.setFont("Courier", 11)
        pdf.drawString(left + 57 * mm, y + 2 * mm, "" if value is None else str(value))
        y -= 10 * mm

    # Checkboxes: a field Content Understanding reads as a selection mark, not text.
    pdf.setFont("Helvetica", 9)
    pdf.drawString(left, y + 1.5 * mm, "Police report available")
    for i, option in enumerate(["YES", "NO"]):
        x = left + 55 * mm + i * 25 * mm
        pdf.rect(x, y + 1 * mm, 4 * mm, 4 * mm)
        pdf.drawString(x + 6 * mm, y + 1.5 * mm, option)
        if fields["police_report_available"] == option:
            pdf.line(x, y + 1 * mm, x + 4 * mm, y + 5 * mm)
            pdf.line(x, y + 5 * mm, x + 4 * mm, y + 1 * mm)
    y -= 14 * mm

    pdf.drawString(left, y, "What happened")
    pdf.rect(left, y - 32 * mm, 170 * mm, 29 * mm)
    text = pdf.beginText(left + 2 * mm, y - 9 * mm)
    text.setFont("Courier", 10)
    line = ""
    for word in fields["description"].split():
        if len(line) + len(word) > 75:
            text.textLine(line)
            line = ""
        line += word + " "
    text.textLine(line)
    pdf.drawText(text)
    y -= 45 * mm

    pdf.drawString(left, y, "I confirm the information above is true.  Signature: ______________________")
    pdf.showPage()
    pdf.save()
    return buf.getvalue()


def to_scan(pdf_bytes: bytes, rng: random.Random) -> bytes:
    page = pymupdf.open(stream=pdf_bytes, filetype="pdf")[0]
    pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
    img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    img = img.rotate(rng.uniform(-2.5, 2.5), expand=True, fillcolor=235, resample=Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 0.9)))
    noise = Image.effect_noise(img.size, rng.uniform(18, 30))
    img = Image.blend(img, noise, 0.12)
    out = io.BytesIO()
    img.save(out, format="PDF", resolution=150)
    return out.getvalue()


def main() -> None:
    rng = random.Random(SEED)
    db = sqlite3.connect(DATA / "claims.db")
    db.row_factory = sqlite3.Row
    claims = [dict(r) for r in db.execute("SELECT * FROM claims ORDER BY claim_id")]
    selected = sorted(rng.sample(claims, FORM_COUNT), key=lambda c: c["claim_id"])
    scans = {c["claim_id"] for c in rng.sample(selected, SCAN_COUNT)}

    TARGET.mkdir(exist_ok=True)
    for old in TARGET.glob("CLM-*"):
        old.unlink()
    for c in selected:
        fields = expected_fields(c)
        pdf = render_pdf(fields)
        if c["claim_id"] in scans:
            pdf = to_scan(pdf, rng)
        (TARGET / f"{c['claim_id']}.pdf").write_bytes(pdf)
        meta = {"scan": c["claim_id"] in scans, "fields": fields}
        (TARGET / f"{c['claim_id']}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Wrote {len(selected)} forms ({len(scans)} scans) to {TARGET.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
