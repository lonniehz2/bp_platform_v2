# -*- coding: utf-8 -*-
import os, sys
import pdfplumber
from docx import Document

base = r"D:\Work\业务平台开发"
outdir = r"D:\Work\业务平台开发\_调研\_gz"

def dump_pdf(path, name):
    lines=[]
    with pdfplumber.open(path) as pdf:
        lines.append(f"### FILE: {name}  pages={len(pdf.pages)}")
        for i,pg in enumerate(pdf.pages, 1):
            lines.append(f"\n===== PAGE {i} =====")
            t = pg.extract_text() or ""
            lines.append(t)
            tables = pg.extract_tables()
            for ti,tb in enumerate(tables):
                lines.append(f"--- TABLE {ti+1} ---")
                for row in tb:
                    lines.append(" | ".join("" if c is None else c.replace("\n"," ") for c in row))
            imgs = pg.images
            if imgs:
                lines.append(f"[page {i} images: {len(imgs)}]")
    return "\n".join(lines)

def dump_docx(path, name):
    d = Document(path)
    lines=[f"### FILE: {name}  paragraphs={len(d.paragraphs)} tables={len(d.tables)}"]
    # iterate body in order
    from docx.oxml.ns import qn
    body = d.element.body
    ti=0; pi=0
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            # find matching paragraph
            from docx.text.paragraph import Paragraph
            p = Paragraph(child, d)
            if p.text.strip():
                lines.append(p.text)
            pi+=1
        elif child.tag == qn('w:tbl'):
            from docx.table import Table
            t = Table(child, d)
            lines.append(f"--- TABLE {ti+1} ({len(t.rows)}x{len(t.columns)}) ---")
            for row in t.rows:
                cells=[]
                for c in row.cells:
                    cells.append(c.text.replace("\n"," ").strip())
                lines.append(" | ".join(cells))
            ti+=1
    # images
    import zipfile
    z=zipfile.ZipFile(path)
    med=[n for n in z.namelist() if n.startswith('word/media/')]
    lines.append(f"[docx media count: {len(med)}]")
    return "\n".join(lines)

jobs = [
    ("云门道智慧物业系统简介.pdf", dump_pdf, "pdf"),
    ("云门道智慧物业系统操作指南.pdf", dump_pdf, "pdf"),
    ("云门道智慧物业系统操作日常问答.pdf", dump_pdf, "pdf"),
    ("云门道智慧物业快速入门指南.docx", dump_docx, "docx"),
]
for fn, f, kind in jobs:
    p = os.path.join(base, fn)
    print("doing", fn, flush=True)
    try:
        txt = f(p, fn)
    except Exception as e:
        txt = f"ERROR {type(e).__name__}: {e}"
    outp = os.path.join(outdir, os.path.splitext(fn)[0] + ".txt")
    open(outp, "w", encoding="utf-8").write(txt)
    print("  ->", outp, len(txt), "chars")
