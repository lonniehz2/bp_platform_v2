import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grab import fetch, OUT

urls = [
    "https://www.byteox.com/product/product/_payload.json",
    "https://www.byteox.com/publicHousing/_payload.json",
    "https://www.byteox.com/customer/_payload.json",
    "https://www.byteox.com/_payload.json",
    "https://www.byteox.com/robots.txt",
    "https://www.byteox.com/sitemap.xml",
]
for u in urls:
    try:
        t = fetch(u, timeout=45)
    except Exception as e:
        print(f"FAIL {u} :: {e}")
        continue
    name = re.sub(r'[^A-Za-z0-9]+', '_', u)[-70:]
    p = os.path.join(OUT, name + ".raw")
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
    print(f"OK {u} len={len(t)} -> {p}")
