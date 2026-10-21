import re, os, sys, glob
OUT = r"D:\Work\业务平台开发\_调研\_raw"
hrefs = set()
for fp in glob.glob(os.path.join(OUT, "*.html")):
    h = open(fp, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'href="([^"]+)"', h):
        hrefs.add(m.group(1))
for u in sorted(hrefs):
    print(u)
