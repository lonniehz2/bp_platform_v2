import re, os
from lxml import html as LH
OUT = r"D:\Work\业务平台开发\_调研\_raw"
h = open(os.path.join(OUT, "https_www_byteox_com_.html"), encoding="utf-8").read()
doc = LH.fromstring(h)

print("=== ALL <a> with text (nav+footer) ===")
seen = set()
for a in doc.iter("a"):
    href = a.get("href") or ""
    txt = " ".join(a.text_content().split())
    if not txt:
        continue
    key = (href, txt)
    if key in seen:
        continue
    seen.add(key)
    if href.startswith("/_nuxt"):
        continue
    print(f"{txt!r:60} -> {href}")

print("\n=== percentum blocks ===")
for el in doc.cssselect(".percentum"):
    # walk up to parent container
    par = el.getparent()
    gp = par.getparent() if par is not None else None
    txt = " ".join(gp.text_content().split()) if gp is not None else ""
    print(repr(" ".join(el.text_content().split())), "| ctx:", txt[:80])
