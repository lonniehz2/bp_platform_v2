# -*- coding: utf-8 -*-
import os, sys, io
import pypdfium2 as pdfium
import pypdf

FILES = [
    ("软件系统", r"D:\Work\eLock\软件系统.pdf"),
    ("产品介绍", r"D:\Work\eLock\产品介绍.pdf"),
    ("业务分布", r"D:\Work\海报\业务分布.pdf"),
    ("企业实力", r"D:\Work\海报\企业实力.pdf"),
]
OUT = r"D:\Work\业务平台开发\_调研\_extract\img"
os.makedirs(OUT, exist_ok=True)

for name, path in FILES:
    doc = pdfium.PdfDocument(path)
    for i in range(len(doc)):
        page = doc[i]
        w, h = page.get_size()
        print(name, "pagesize", round(w), round(h))
        scale = 2400.0 / max(w, h)
        bmp = page.render(scale=scale)
        pil = bmp.to_pil()
        p = os.path.join(OUT, f"{name}_render.png")
        pil.save(p)
        print("  saved", p, pil.size)
    doc.close()
    # embedded images
    r = pypdf.PdfReader(path)
    for pi, pg in enumerate(r.pages):
        try:
            for ii, im in enumerate(pg.images):
                p = os.path.join(OUT, f"{name}_embed_p{pi+1}_{ii}_{im.name}")
                with open(p, "wb") as f:
                    f.write(im.data)
                print("  embed", p, len(im.data))
        except Exception as e:
            print("  embed FAIL", e, file=sys.stderr)
