# -*- coding: utf-8 -*-
import os, zipfile
from docx import Document
from docx.oxml.ns import qn
p = r"D:\Work\业务平台开发\云门道智慧物业快速入门指南.docx"
d = Document(p)
out=[]
for i,pp in enumerate(d.paragraphs):
    out.append(f"[{i}] style={pp.style.name!r} :: {pp.text}")
open(r"D:\Work\业务平台开发\_调研\_gz\kuaijie_paras.txt","w",encoding="utf-8").write("\n".join(out))
print("\n".join(out))
z=zipfile.ZipFile(p)
med=[n for n in z.namelist() if n.startswith('word/media/')]
print("MEDIA", len(med))
for n in med: print(n, z.getinfo(n).file_size)
