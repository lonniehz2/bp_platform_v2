import io
p=r'src\pages\DeviceBinding.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('{{ s.spacePath }}（{{ s.spaceType }}）','{{ s.spaceName }}（{{ s.spaceType }}）')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('space label')
