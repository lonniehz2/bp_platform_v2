import os,re,json
root='src/pages'
for fn in sorted(os.listdir(root)):
 if not fn.endswith('.vue'): continue
 s=open(os.path.join(root,fn),encoding='utf-8').read()
 selects=len(re.findall(r'<select\b',s))
 buttons=re.findall(r'<button[^>]*>(.*?)</button>',s,re.S)
 btns=[]
 for b in buttons:
  t=re.sub(r'<[^>]+>','',b); t=re.sub(r'\s+',' ',t).strip()
  if t and t not in btns: btns.append(t)
 print(f'{fn}\tselects={selects}\tbuttons={len(btns)}\t'+'|'.join(btns[:12]))
