"""Build the architecture PDF from content.html and the SVG diagrams.

Usage: python build.py
Writes ../claims-assistant-architecture.pdf (via headless Chrome).
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

html = re.sub(r"\{\{svg:([\w-]+)\}\}", lambda m: (HERE / "svg" / f"{m[1]}.svg").read_text(encoding="utf-8"),
              (HERE / "content.html").read_text(encoding="utf-8"))

tmp = HERE / "_print.html"
tmp.write_text(html, encoding="utf-8")
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=20000",
                f"--print-to-pdf={HERE.parent / 'claims-assistant-architecture.pdf'}", tmp.resolve().as_uri()],
               check=True, stderr=subprocess.DEVNULL)
tmp.unlink()
print("built claims-assistant-architecture.pdf")
