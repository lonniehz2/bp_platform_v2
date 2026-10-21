# -*- coding: utf-8 -*-
import os
import pypdfium2 as pdfium
from PIL import Image

FILES = [
    ("软件系统", r"D:\Work\eLock\软件系统.pdf"),
    ("产品介绍", r"D:\Work\eLock\产品介绍.pdf"),
    ("业务分布", r"D:\Work\海报\业务分布.pdf"),
    ("企业实力", r"D:\Work\海报\企业实力.pdf"),
]
OUT = r"D:\Work\业务平台开发\_调研\_extract\tiles"
os.makedirs(OUT, exist_ok=True)

TARGET_W = 1700
TILE_H = 1300
OVERLAP = 120

for name, path in FILES:
    doc = pdfium.PdfDocument(path)
    page = doc[0]
    w, h = page.get_size()
    scale = TARGET_W / w
    pil = page.render(scale=scale).to_pil().convert("RGB")
    W, H = pil.size
    y = 0
    idx = 1
    while y < H:
        y2 = min(y + TILE_H, H)
        tile = pil.crop((0, y, W, y2))
        p = os.path.join(OUT, f"{name}_t{idx:02d}.png")
        tile.save(p, optimize=True)
        print(p, tile.size, "y", y, y2)
        idx += 1
        if y2 >= H:
            break
        y = y2 - OVERLAP
    doc.close()
