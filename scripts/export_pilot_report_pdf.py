"""
Exports a Markdown file under output/ to a same-named PDF, with figures
embedded. Pure-Python (markdown + xhtml2pdf), since pandoc/wkhtmltopdf/
weasyprint's native dependencies are not available on this machine.

Run with:
    .venv/bin/python scripts/export_pilot_report_pdf.py [NAME.md]
    (defaults to PILOT_REPORT.md if no argument is given)
"""
from __future__ import annotations

import sys
from pathlib import Path

import markdown
from xhtml2pdf import pisa

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "output"

CSS = """
<style>
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.4; }
h1 { font-size: 18pt; margin-top: 0; }
h2 { font-size: 14pt; margin-top: 18pt; border-bottom: 1px solid #ccc; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin-top: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9pt; }
th, td { border: 1px solid #999; padding: 3pt 6pt; text-align: left; }
th { background-color: #eee; }
img { max-width: 480pt; margin: 6pt 0; }
code { font-family: Courier, monospace; background-color: #f4f4f4; }
hr { margin-top: 14pt; }
</style>
"""


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "PILOT_REPORT.md"
    md_path = OUT_DIR / name
    text = md_path.read_text()
    html_body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    html = f"<html><head>{CSS}</head><body>{html_body}</body></html>"

    pdf_path = md_path.with_suffix(".pdf")
    with open(pdf_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f, path=str(md_path))

    if result.err:
        print(f"Errors during PDF generation: {result.err}", file=sys.stderr)
        sys.exit(1)
    print(f"Saved {pdf_path}")


if __name__ == "__main__":
    main()
