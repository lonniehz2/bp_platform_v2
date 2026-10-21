import sys, os, re, html, urllib.request, urllib.error, json, time

OUT = r"D:\Work\业务平台开发\_调研\_raw"
os.makedirs(OUT, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
        try:
            return data.decode(enc, errors="replace")
        except Exception:
            return data.decode("utf-8", errors="replace")

def to_text(h):
    h = re.sub(r'(?is)<script.*?</script>', ' ', h)
    h = re.sub(r'(?is)<style.*?</style>', ' ', h)
    h = re.sub(r'(?is)<noscript.*?</noscript>', ' ', h)
    h = re.sub(r'(?is)<svg.*?</svg>', ' ', h)
    h = re.sub(r'(?is)<!--.*?-->', ' ', h)
    h = re.sub(r'(?i)</(p|div|li|h1|h2|h3|h4|h5|h6|tr|section|article|td|th|ul|ol|table|header|footer|main|span|a|strong|em)>', '\n', h)
    h = re.sub(r'(?i)<br\s*/?>', '\n', h)
    h = re.sub(r'(?s)<[^>]+>', ' ', h)
    h = html.unescape(h)
    lines = [re.sub(r'[ \t\xa0]+', ' ', ln).strip() for ln in h.split('\n')]
    lines = [ln for ln in lines if ln]
    return '\n'.join(lines)

def grab(url, name=None, save_raw=True):
    name = name or re.sub(r'[^A-Za-z0-9]+', '_', url)[-80:]
    try:
        h = fetch(url)
    except Exception as e:
        print(f"FAIL {url} :: {e}")
        return None
    if save_raw:
        with open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8") as f:
            f.write(h)
    t = to_text(h)
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(t)
    print(f"OK {url} html={len(h)} text={len(t)} -> {name}.txt")
    return t

if __name__ == "__main__":
    for u in sys.argv[1:]:
        grab(u)
