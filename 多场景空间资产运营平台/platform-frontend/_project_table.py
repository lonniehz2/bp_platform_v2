import io
p=r'src\pages\Projects.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''          <thead><tr><th>项目编码</th><th>项目名称</th><th>经营模式</th><th>模板</th><th>状态</th><th>操作</th></tr></thead>''','''          <thead><tr><th>项目编码</th><th>项目名称</th><th>地址</th><th>联系人</th><th>总建筑面积</th><th>产权类型</th><th>经营模式</th><th>模板</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.businessMode }}</td>
              <td>{{ p.templateName || p.spaceTemplateId }}</td>''','''              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.totalArea || '-' }}</td>
              <td>{{ p.propertyType || '-' }}</td><td>{{ p.businessMode }}</td>
              <td>{{ p.templateName || p.spaceTemplateId }}</td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('project table')
