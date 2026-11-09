import os,re
root='src/pages'
for fn in sorted(os.listdir(root)):
 if not fn.endswith('.vue'): continue
 s=open(os.path.join(root,fn),encoding='utf-8').read()
 # collect function bodies roughly
 for m in re.finditer(r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{',s):
  start=m.end(); depth=1; i=start
  while i<len(s) and depth:
   if s[i]=='{': depth+=1
   elif s[i]=='}': depth-=1
   i+=1
  body=s[start:i]
  if re.search(r'api\.\w+\(',body) and re.search(r'create|update|delete|remove|adjust|pay|refund|submit|approve|reject|close|discard|withdraw|activate|bind|unbind|import|allocate|cancel|publish|offline|book|confirm|resolve|save|toggle|revoke|complete|handle',body,re.I):
   if 'load()' not in body and 'reload' not in body and 'await load' not in body:
    # ignore functions that just return or modal close
    print(fn,m.group(1))
