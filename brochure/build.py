"""Genera brochure HTML autonoma + PDF stampabile (A4 orizzontale, fronte/retro)."""
import json
import re
import subprocess
from pathlib import Path

DIR = Path(__file__).parent
OUT = Path("/app/frontend/public/brochure")
OUT.mkdir(parents=True, exist_ok=True)

icons = json.loads((DIR / "icons.json").read_text())
qr = re.sub(r"<\?xml[^>]*\?>", "", (DIR / "qr.svg").read_text())
qr = re.sub(r'width="[^"]*" height="[^"]*"', "", qr, count=1)

html = (DIR / "brochure.template.html").read_text()
html = html.replace("{{QR}}", qr)
html = re.sub(r"\{\{(\w+)\}\}", lambda m: icons[m.group(1)], html)

out_html = OUT / "brochure-portale-sla.html"
out_html.write_text(html)
subprocess.run([
    "chromium", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
    "--virtual-time-budget=8000", f"--print-to-pdf={OUT / 'brochure-portale-sla.pdf'}", f"file://{out_html}",
], check=True, capture_output=True)
print("OK", out_html)
