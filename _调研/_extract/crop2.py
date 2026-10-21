# -*- coding: utf-8 -*-
import os
import pypdfium2 as pdfium
from PIL import Image

OUT = r"D:\Work\业务平台开发\_调研\_extract\crops"
os.makedirs(OUT, exist_ok=True)

path = r"D:\Work\eLock\软件系统.pdf"
doc = pdfium.PdfDocument(path)
page = doc[0]
w, h = page.get_size()
SCALE = 3400.0 / w
pil = page.render(scale=SCALE).to_pil().convert("RGB")

def crop(name, x1, y1, x2, y2, up=2):
    im = pil.crop((x1 * 2, y1 * 2, x2 * 2, y2 * 2))
    im = im.resize((im.width * up, im.height * up), Image.LANCZOS)
    p = os.path.join(OUT, name + ".png")
    im.save(p)
    print(p, im.size)

# role/permission tier diagram (1700-wide coords)
crop("perm_roles", 360, 2020, 990, 2320, 3)
crop("perm_table", 360, 2280, 990, 2580, 3)
doc.close()
