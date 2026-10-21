# -*- coding: utf-8 -*-
import os
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
src=r"D:\Work\业务平台开发\_调研\_公租房图\image5.emf"
try:
    im=Image.open(src)
    print("size",im.size,"mode",im.mode,"format",im.format)
    scale=4
    im2=im.convert("RGB").resize((im.size[0]*scale, im.size[1]*scale), Image.LANCZOS)
    dst=r"D:\Work\业务平台开发\_调研\_gz\image5_fromPIL.png"
    im2.save(dst)
    print("saved",dst,os.path.getsize(dst))
except Exception as e:
    print("PIL FAIL:",type(e).__name__,e)
