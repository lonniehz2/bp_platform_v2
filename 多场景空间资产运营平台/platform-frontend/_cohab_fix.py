import io
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read().replace('{{ c.validStart || c.startDate || \'\' }}','{{ c.startDate || \'\' }}')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fix')
