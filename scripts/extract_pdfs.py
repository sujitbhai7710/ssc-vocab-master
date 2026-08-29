#!/usr/bin/env python3
"""Extract text from the 3 grammar PDFs using pdfplumber.
Outputs plain text files to /home/z/my-project/work/pdf_text/.
"""
import pdfplumber, os, sys

PDFS = {
    "rani-maam": "/home/z/my-project/ssc-txt/rani-maam.pdf",
    "error-spotting": "/home/z/my-project/ssc-txt/error spotting.pdf",
    "100-grammar-rules": "/home/z/my-project/ssc-txt/100-grammar-rules.pdf",
}
OUT = "/home/z/my-project/work/pdf_text"
os.makedirs(OUT, exist_ok=True)

for name, path in PDFS.items():
    print(f"=== {name} ({path}) ===", flush=True)
    parts = []
    with pdfplumber.open(path) as pdf:
        print(f"  pages: {len(pdf.pages)}", flush=True)
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            parts.append(f"\n\n===== PAGE {i+1} =====\n{txt}")
    text = "\n".join(parts)
    outp = os.path.join(OUT, f"{name}.txt")
    with open(outp, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  -> {outp}  ({len(text)} chars)", flush=True)
print("DONE")
