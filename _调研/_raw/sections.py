import os, re, glob
OUT = r"D:\Work\业务平台开发\_调研\_raw"

def content(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    try:
        s = lines.index("返回顶部") + 1
    except ValueError:
        s = 0
    # skip leading 返回顶部/dup markers
    while s < len(lines) and lines[s].strip() in ("返回顶部", "", "\uE731"):
        s += 1
    e = len(lines)
    for i in range(s, len(lines)):
        if lines[i].strip().startswith("10000"):
            e = i
            break
    return "\n".join(lines[s:e])

names = ["serviced","shortRent","corporateDorm","businessPark","talentHousing","studentDorm",
         "about","news","download","prod_jdf","prod_tfzs","prod_yxs","https_www_byteox_com_"]
for n in names:
    p = os.path.join(OUT, n + ".txt")
    if not os.path.exists(p):
        print(f"### MISSING {n}"); continue
    print(f"\n{'='*70}\n### {n}\n{'='*70}")
    print(content(p))
