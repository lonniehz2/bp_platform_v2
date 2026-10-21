# -*- coding: utf-8 -*-
import sys, os, io, json
import pypdf

FILES = [
    ("软件系统_eLock", r"D:\Work\eLock\软件系统.pdf"),
    ("产品介绍", r"D:\Work\eLock\产品介绍.pdf"),
    ("业务分布", r"D:\Work\海报\业务分布.pdf"),
    ("企业实力", r"D:\Work\海报\企业实力.pdf"),
    ("云门道e锁-厂家方案客户版", r"D:\Work\业务平台开发\云门道e锁-智能锁厂家一站式核心方案（客户版）.pdf"),
]

OUT = r"D:\Work\业务平台开发\_调研\_extract"
os.makedirs(OUT, exist_ok=True)

report = []
for name, path in FILES:
    r = pypdf.PdfReader(path)
    pages = []
    for i, p in enumerate(r.pages):
        try:
            t = p.extract_text() or ""
        except Exception as e:
            t = ""
            print("ERR page", i, e, file=sys.stderr)
        pages.append(t)
    total = sum(len(t.strip()) for t in pages)
    report.append({
        "name": name, "path": path, "pages": len(r.pages),
        "total_chars": total,
        "stripped_pages": sum(1 for t in pages if len(t.strip()) < 10),
    })
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
        for i, t in enumerate(pages):
            f.write("\n===== PAGE %d / %d =====\n" % (i + 1, len(pages)))
            f.write(t.strip() + "\n")

print(json.dumps(report, ensure_ascii=False, indent=2))
