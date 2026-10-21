# -*- coding: utf-8 -*-
import zipfile, re
from lxml import etree
p = r"D:\Work\业务平台开发\云门道智慧物业快速入门指南.docx"
z = zipfile.ZipFile(p)
print(z.namelist())
xml = z.read('word/document.xml').decode('utf-8','ignore')
print("doc.xml len", len(xml))
print("txbxContent count:", xml.count('txbxContent'))
# clean dump
root = etree.fromstring(z.read('word/document.xml'))
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
txts = root.findall('.//'+W+'t')
full = "\n".join((t.text or '') for t in txts)
print("total w:t count", len(txts), "chars", len(full))
open(r"D:\Work\业务平台开发\_调研\_gz\kuaijie_alltext.txt","w",encoding="utf-8").write(full)
print(full[:4000])
