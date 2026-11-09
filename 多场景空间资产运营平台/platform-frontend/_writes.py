import os,re
root='src/pages'
for fn in sorted(os.listdir(root)):
 if not fn.endswith('.vue'): continue
 s=open(os.path.join(root,fn),encoding='utf-8').read()
 calls=sorted(set(re.findall(r'api\.([A-Za-z0-9_]+)\s*\(',s)))
 writes=[c for c in calls if re.search(r'create|update|delete|remove|adjust|pay|refund|submit|approve|reject|close|discard|withdraw|activate|bind|unbind|import|allocate|cancel|publish|offline|book|confirm|resolve|save|toggle|revoke|complete|handle',c,re.I)]
 print(fn+': '+', '.join(writes))
