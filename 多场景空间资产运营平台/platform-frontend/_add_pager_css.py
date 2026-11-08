import io
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.pager' not in s:
 s += '''

.pager { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; gap: 12px; }
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('pager css')
