# -*- coding: utf-8 -*-
import os
import pypdfium2 as pdfium
from PIL import Image

OUT = r"D:\Work\业务平台开发\_调研\_extract\crops"
os.makedirs(OUT, exist_ok=True)

path = r"D:\Work\海报\企业实力.pdf"
doc = pdfium.PdfDocument(path)
page = doc[0]
w, h = page.get_size()
SCALE = 3400.0 / w
pil = page.render(scale=SCALE).to_pil().convert("RGB")
W, H = pil.size
print("full", W, H)

# 1700-wide coords -> factor 2
def crop(name, x1, y1, x2, y2, up=2):
    box = (x1 * 2, y1 * 2, x2 * 2, y2 * 2)
    im = pil.crop(box)
    im = im.resize((im.width * up, im.height * up), Image.LANCZOS)
    p = os.path.join(OUT, name + ".png")
    im.save(p)
    print(p, im.size)

# top row of software copyright grid (names column)
crop("qr_top_left", 80, 2810, 470, 3010, 3)
crop("qr_top_mid", 80, 2960, 470, 3170, 3)
crop("qr_bottom_left", 80, 3230, 470, 3430, 3)
crop("qr_bottom_mid", 80, 3380, 470, 3600, 3)
doc.close()
