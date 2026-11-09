import os,re
root='src/pages'
for fn in sorted(os.listdir(root)):
 if not fn.endswith('.vue'): continue
 s=open(os.path.join(root,fn),encoding='utf-8').read()
 fields=[]
 for m in re.finditer(r'<div class="field"[^>]*>(.*?)</div>',s,re.S):
  block=m.group(1)
  lm=re.search(r'<label[^>]*>(.*?)</label>',block,re.S)
  sm=re.search(r'<select[^>]*v-model="([^"]+)"[^>]*>(.*?)</select>',block,re.S)
  if lm and sm:
   label=re.sub(r'<[^>]+>','',lm.group(1)).strip()
   model=sm.group(1)
   opts=re.findall(r'<option[^>]*v-for="([^"]+)"',sm.group(2))
   fields.append(f'{label}[{model}]{" v-for:"+opts[0] if opts else ""}')
 if fields:
  print(fn+': '+'; '.join(fields))
