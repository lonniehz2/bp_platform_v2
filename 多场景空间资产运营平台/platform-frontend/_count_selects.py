import os,re
root='src/pages'; total=0; pages=0
for fn in os.listdir(root):
 if not fn.endswith('.vue'): continue
 s=open(os.path.join(root,fn),encoding='utf-8').read(); n=len(re.findall(r'<select\b',s)); total+=n; pages+=1 if n else 0
print('pages',pages,'selects',total)
