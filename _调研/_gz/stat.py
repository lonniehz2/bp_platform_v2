# -*- coding: utf-8 -*-
import zipfile, os, sys, collections
from docx import Document
from docx.shared import Emu

p = r"D:\Work\业务平台开发\_调研\公租房管理方案.docx"
z = zipfile.ZipFile(p)
names = z.namelist()
media = [n for n in names if n.startswith('word/media/')]
print("=== ZIP entries:", len(names))
print("=== media count (zip):", len(media))
ext = collections.Counter(os.path.splitext(n)[1].lower() for n in media)
print("=== media ext:", dict(ext))
print("=== total media bytes:", sum(z.getinfo(n).file_size for n in media))

d = Document(p)
print("=== paragraphs:", len(d.paragraphs))
print("=== tables:", len(d.tables))
print("=== sections:", len(d.sections))
# inline shapes
try:
    print("=== inline_shapes:", len(d.inline_shapes))
except Exception as e:
    print("inline_shapes err", e)

# count drawings in document.xml
xml = z.read('word/document.xml').decode('utf-8', 'ignore')
print("=== <w:drawing> occurrences:", xml.count('<w:drawing>'))
print("=== <w:pict> occurrences:", xml.count('<w:pict>'))
print("=== <w:tbl> occurrences:", xml.count('<w:tbl>'))
print("=== doc.xml size:", len(xml))

# total text length
txt = "\n".join(pp.text for pp in d.paragraphs)
print("=== total paragraph text chars:", len(txt.strip()))
print("=== total table cell chars:", sum(len(c.text) for t in d.tables for r in t.rows for c in r.cells))

# media sizes detail
print("--- media detail (top 60 by size) ---")
for n in sorted(media, key=lambda x: -z.getinfo(x).file_size)[:60]:
    print(z.getinfo(n).file_size, n, "compressed:", z.getinfo(n).compress_size)
