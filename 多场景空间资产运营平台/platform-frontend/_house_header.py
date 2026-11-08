import io
p=r'src\pages\Houses.vue'
s=io.open(p,encoding='utf-8').read().replace('<thead><tr><th>房源编码</th><th>名称</th><th>资产类型</th><th>面积</th><th>房态</th></tr></thead>','<thead><tr><th>房源编码</th><th>名称</th><th>户型</th><th>朝向</th><th>楼层</th><th>建筑面积</th><th>套内面积</th><th>房态</th><th>操作</th></tr></thead>')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('house header')
