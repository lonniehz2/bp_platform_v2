import io
p=r'src\pages\PlatformInfo.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const error = ref('')","const error = ref('')\nconst origin = window.location.origin")
s=s.replace('{{ location.origin }}','{{ origin }}')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('platform info fix')
