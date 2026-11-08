import io,json
p=r'package.json'
d=json.load(io.open(p,encoding='utf-8'))
d['dependencies']['echarts']='^5.6.0'
io.open(p,'w',encoding='utf-8',newline='').write(json.dumps(d,ensure_ascii=False,indent=2))
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.chart {' not in s:
 s += '''

.chart { width: 100%; height: 240px; }
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('echarts dep/css')
