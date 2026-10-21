# -*- coding: utf-8 -*-
import os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
out = r"D:\Work\业务平台开发\_调研\_公租房图"
for n in sorted(os.listdir(out)):
    p = os.path.join(out, n)
    try:
        im = Image.open(p)
        print(f"{n}\t{im.size}\t{im.mode}\t{im.format}")
    except Exception as e:
        print(f"{n}\tERROR {e}")
