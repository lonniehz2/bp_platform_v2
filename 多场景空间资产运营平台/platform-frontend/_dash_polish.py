import io
p=r'src\pages\Dashboard.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('<div class="grid cards">\n        <div class="card"><div class="label">项目数</div>','<div class="grid cards" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">\n        <div class="card"><div class="label">项目数</div>')
s=s.replace("grid: { left: 40, right: 16, top: 30, bottom: 30 },","grid: { left: 72, right: 18, top: 30, bottom: 30 },")
s=s.replace("yAxis: { type: 'value', axisLabel: { color: c.text }, splitLine: { lineStyle: { color: c.line } } },","yAxis: { type: 'value', axisLabel: { color: c.text, formatter: v => Math.abs(v) >= 10000 ? (v / 10000).toFixed(1) + '万' : v }, splitLine: { lineStyle: { color: c.line } } },")
s=s.replace("grid: { left: 70, right: 24, top: 10, bottom: 22 },","grid: { left: 92, right: 24, top: 10, bottom: 22 },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('dashboard polish')
