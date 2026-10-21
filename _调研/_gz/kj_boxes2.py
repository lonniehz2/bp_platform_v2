# -*- coding: utf-8 -*-
import zipfile, re
from lxml import etree
p = r"D:\Work\业务平台开发\云门道智慧物业快速入门指南.docx"
z = zipfile.ZipFile(p)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
V='{urn:schemas-microsoft-com:vml}'
root = etree.fromstring(z.read('word/document.xml'))
body = root.find(W+'body')

out=[]
for shp in body.iter(V+'shape'):
    style = shp.get('style','')
    m = re.search(r'left:(-?\d+);top:(-?\d+)', style)
    if not m: 
        m2 = re.search(r'left:(-?\d+)pt;top:(-?\d+)pt', style)
        if not m2: continue
        L,T = int(m2.group(1)), int(m2.group(2))
    else:
        L,T = int(m.group(1)), int(m.group(2))
    tb = shp.find('.//'+W+'txbxContent')
    if tb is None: continue
    s=''.join((t.text or '') for t in tb.iter(W+'t')).strip()
    if not s: continue
    out.append((T,L,s))
out.sort()
for T,L,s in out:
    print(f"T={T:6d} L={L:6d} :: {s}")
