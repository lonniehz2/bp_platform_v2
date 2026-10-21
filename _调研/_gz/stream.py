# -*- coding: utf-8 -*-
import zipfile, re, os
from docx import Document
from lxml import etree

p = r"D:\Work\业务平台开发\_调研\公租房管理方案.docx"
z = zipfile.ZipFile(p)
xml = z.read('word/document.xml').decode('utf-8','ignore')

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
V='{urn:schemas-microsoft-com:vml}'
nsmap={'w':W[1:-1],'r':R[1:-1],'a':A[1:-1],'v':V[1:-1]}

root = etree.fromstring(z.read('word/document.xml'))
body = root.find(W+'body')

# rels
rels = etree.fromstring(z.read('word/_rels/document.xml.rels'))
relmap={}
for rel in rels:
    relmap[rel.get('Id')] = rel.get('Target')

out=[]
def walk(el, depth=0, path=''):
    for child in el:
        tag = etree.QName(child).localname
        if tag=='p':
            # text
            texts = child.findall('.//'+W+'t')
            t = ''.join(x.text or '' for x in texts)
            # find images in this paragraph
            imgs=[]
            for blip in child.findall('.//'+A+'blip'):
                rid = blip.get(R+'embed')
                imgs.append(relmap.get(rid, rid))
            for im in child.findall('.//'+V+'imagedata'):
                rid = im.get(R+'id')
                imgs.append('VML:'+str(relmap.get(rid, rid)))
            style = child.find(W+'pPr/'+W+'pStyle')
            st = style.get(W+'val') if style is not None else ''
            numpr = child.find(W+'pPr/'+W+'numPr')
            bullet = ' [LIST]' if numpr is not None else ''
            if t.strip() or imgs:
                out.append(f"[P] style={st}{bullet} IMG={imgs if imgs else ''}\n    {t}")
            else:
                out.append(f"[P-EMPTY] style={st} IMG={imgs if imgs else ''}")
        elif tag=='tbl':
            out.append("[TABLE START]")
            for ri,row in enumerate(child.findall(W+'tr')):
                cells=[]
                for cell in row.findall(W+'tc'):
                    ct=' '.join(''.join(x.text or '' for x in pp.findall('.//'+W+'t')) for pp in cell.findall(W+'p'))
                    cells.append(ct)
                out.append(f"  ROW{ri}: " + " | ".join(cells))
            out.append("[TABLE END]")
        elif tag=='sdt':
            walk(child, depth+1, path)
        else:
            walk(child, depth+1, path)

walk(body)
open(r"D:\Work\业务平台开发\_调研\_gz\text_stream.txt","w",encoding="utf-8").write("\n".join(out))
print("lines:", len(out))
print("\n".join(out))
