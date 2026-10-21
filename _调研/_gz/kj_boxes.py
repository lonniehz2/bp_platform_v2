# -*- coding: utf-8 -*-
import zipfile
from lxml import etree
p = r"D:\Work\业务平台开发\云门道智慧物业快速入门指南.docx"
z = zipfile.ZipFile(p)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WP='{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
V='{urn:schemas-microsoft-com:vml}'
root = etree.fromstring(z.read('word/document.xml'))
body = root.find(W+'body')

def pos_of(el):
    # search ancestors for anchor position
    anc = el
    while anc is not None:
        for tag in ('anchor','inline'):
            n = anc.find('.//'+WP+tag)
            if n is not None:
                x = n.find(WP+'positionH/'+WP+'posOffset')
                y = n.find(WP+'positionV/'+WP+'posOffset')
                return (x.text if x is not None else '?', y.text if y is not None else '?')
        sha = anc.find('.//'+V+'shape')
        if sha is not None:
            st = sha.get('style','')
            return ('VML', st)
        anc = anc.getparent()
    return ('?','?')

out=[]
for tb in body.iter(W+'txbxContent'):
    texts=[(t.text or '') for t in tb.iter(W+'t')]
    s=''.join(texts).strip()
    if not s: continue
    # find ancestor for position
    x,y = pos_of(tb)
    out.append((y,x,s))

def num(v):
    try: return int(v)
    except: return 10**9
out.sort(key=lambda t:(num(t[0]), num(t[1])))
lines=[]
for y,x,s in out:
    lines.append(f"[y={y} x={x}] {s}")
open(r"D:\Work\业务平台开发\_调研\_gz\kj_boxes.txt","w",encoding="utf-8").write("\n".join(lines))
print(len(out),"boxes")
print("\n".join(lines))
