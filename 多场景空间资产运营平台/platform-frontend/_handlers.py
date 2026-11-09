import os,re
root='src/pages'
for fn in sorted(os.listdir(root)):
 if not fn.endswith('.vue'): continue
 s=open(os.path.join(root,fn),encoding='utf-8').read()
 handlers=set(re.findall(r'@click(?:\.stop)?="([A-Za-z_$][\w$]*)\s*(?:\(|")',s))
 defs=set(re.findall(r'(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(',s))
 defs |= set(re.findall(r'const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(',s))
 missing=sorted(h for h in handlers if h not in defs)
 # buttons with no click and no type
 btns=re.findall(r'<button(?![^>]*@click)(?![^>]*type=)[^>]*>(.*?)</button>',s,re.S)
 noclk=[]
 for b in btns:
  t=re.sub(r'<[^>]+>','',b); t=re.sub(r'\s+',' ',t).strip()
  if t: noclk.append(t)
 if missing or noclk:
  print(fn,'missing=',missing,'nohandler=',noclk[:6])
