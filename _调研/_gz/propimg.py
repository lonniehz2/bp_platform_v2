# -*- coding: utf-8 -*-
import os, zipfile, io
from PIL import Image
Image.MAX_IMAGE_PIXELS=None

out = r"D:\Work\业务平台开发\_调研\_gz\propimg"
os.makedirs(out, exist_ok=True)

# 1) docx media
p = r"D:\Work\业务平台开发\云门道智慧物业快速入门指南.docx"
z = zipfile.ZipFile(p)
for n in z.namelist():
    if n.startswith('word/media/') and not n.endswith('/'):
        b = z.read(n)
        tgt = os.path.join(out, 'kj_' + os.path.basename(n))
        open(tgt,'wb').write(b)
        try:
            im = Image.open(io.BytesIO(b)); sz = im.size
        except Exception as e:
            sz = str(e)
        print('kj', os.path.basename(n), len(b), sz)

# 2) pdf xobjects
def pdf_imgs(path, prefix):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages, 1):
            for ii, im in enumerate(page.images):
                print(prefix, 'page', pi, 'img', ii, 'size', im.get('srcsize'), 'w/h', round(im['width'],1), round(im['height'],1), 'name', im.get('name'))
    # also raw xobject dump
    from pypdf import PdfReader
    r = PdfReader(path)
    for pi, page in enumerate(r.pages, 1):
        try:
            res = page['/Resources']
            xo = res.get('/XObject')
            if not xo: continue
            for name in xo:
                obj = xo[name].get_object()
                if obj.get('/Subtype') == '/Image':
                    w = obj.get('/Width'); h = obj.get('/Height')
                    data = obj.get_data()
                    filt = obj.get('/Filter')
                    ext = 'png' if filt == '/FlateDecode' else ('jpg' if filt in ('/DCTDecode','/DCT') else str(filt).replace('/',''))
                    fn = f"{out}\\{prefix}_p{pi}_{name.strip('/')}.{ext}"
                    try:
                        open(fn,'wb').write(data)
                    except Exception as e:
                        print('  write fail', e); continue
                    print(prefix, 'raw page', pi, name, w, h, ext, len(data))
        except Exception as e:
            print(prefix, 'err', e)

pdf_imgs(r"D:\Work\业务平台开发\云门道智慧物业系统简介.pdf", "jj")
pdf_imgs(r"D:\Work\业务平台开发\云门道智慧物业系统操作指南.pdf", "zn")
