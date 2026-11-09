import io
p=r'src\pages\DeviceBinding.vue'
s=io.open(p,encoding='utf-8').read()
old='''<select v-model="form.spaceId"><option value="">请选择</option><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}（{{ s.spaceType }}）</option></select>'''
new='''<TreeSelect v-model="form.spaceId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" placeholder="选择绑定空间" />'''
if old not in s: raise SystemExit('space select not found')
s=s.replace(old,new,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('space tree')
