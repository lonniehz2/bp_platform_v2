# -*- coding: utf-8 -*-
import zipfile, os
from lxml import etree
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def docx_text(p):
    z=zipfile.ZipFile(p); parts=[]
    for n in z.namelist():
        if n.endswith('.xml') and ('document' in n or 'header' in n or 'footer' in n or 'footnotes' in n or 'endnotes' in n or 'comment' in n):
            try:
                r=etree.fromstring(z.read(n))
                parts.append(''.join((t.text or '') for t in r.iter(W+'t')))
            except Exception: pass
    return '\n'.join(parts)

def pdf_text(p):
    import pdfplumber
    out=[]
    with pdfplumber.open(p) as pdf:
        for pg in pdf.pages:
            out.append(pg.extract_text() or '')
    return '\n'.join(out)

base=r"D:\Work\业务平台开发"
main = docx_text(os.path.join(base,r"_调研\公租房管理方案.docx"))
prop = []
for f in ["云门道智慧物业系统简介.pdf","云门道智慧物业系统操作指南.pdf","云门道智慧物业系统操作日常问答.pdf"]:
    prop.append(pdf_text(os.path.join(base,f)))
prop.append(docx_text(os.path.join(base,"云门道智慧物业快速入门指南.docx")))
prop = '\n'.join(prop)
allt = main + '\n' + prop

kws = ["申请","受理","资格","审核","联审","不动产","民政","社保","公积金","轮候","摇号","选房","配租","补贴","减免","滞纳金","年审","复核","腾退","再分配","准入","租金标准","对账","审批流","角色","权限","批量导入","等保","个人信息保护","住建局","住房保障中心","公安"]
print("=== 在【公租房管理方案.docx】中的出现次数 ===")
for k in kws:
    print(f"{k}\t{main.count(k)}")
print("\n=== 在【5 份资料全部】中的出现次数 ===")
for k in kws:
    print(f"{k}\t{allt.count(k)}")
print("\nmain len", len(main), "prop len", len(prop))
