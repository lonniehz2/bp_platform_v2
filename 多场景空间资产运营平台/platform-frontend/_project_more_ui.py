import io
p=r'src\pages\Projects.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("defaultAssetTypeCode: 'PUBLIC_RENTAL', address: '', contactName: '', contactPhone: '', remark: '' })","defaultAssetTypeCode: 'PUBLIC_RENTAL', address: '', contactName: '', contactPhone: '', remark: '', totalArea: 0, landArea: 0, propertyType: '', buildYear: 2020 })")
s=s.replace("      contactPhone: form.contactPhone, remark: form.remark\n    })","      contactPhone: form.contactPhone, remark: form.remark,\n      totalArea: Number(form.totalArea || 0), landArea: Number(form.landArea || 0),\n      propertyType: form.propertyType, buildYear: Number(form.buildYear || 0)\n    })")
s=s.replace('''        <div class="field"><label>联系电话</label><input v-model="form.contactPhone" /></div>''','''        <div class="field"><label>联系电话</label><input v-model="form.contactPhone" /></div>
        <div class="field"><label>总建筑面积</label><input v-model.number="form.totalArea" type="number" /></div>
        <div class="field"><label>占地面积</label><input v-model.number="form.landArea" type="number" /></div>
        <div class="field"><label>产权类型</label><select v-model="form.propertyType"><option value="">未填写</option><option value="STATE">国有</option><option value="COLLECTIVE">集体</option><option value="PRIVATE">私有</option></select></div>
        <div class="field"><label>建成年份</label><input v-model.number="form.buildYear" type="number" /></div>''')
s=s.replace('''            <thead><tr><th>项目编码</th><th>项目名称</th><th>地址</th><th>联系人</th><th>经营模式</th><th>模板</th><th>状态</th><th>操作</th></tr></thead>''','''            <thead><tr><th>项目编码</th><th>项目名称</th><th>地址</th><th>联系人</th><th>总建筑面积</th><th>产权类型</th><th>经营模式</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.businessMode }}</td><td>{{ p.spaceTemplateName || p.templateName }}</td>''','''              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.totalArea || '-' }}</td><td>{{ p.propertyType || '-' }}</td><td>{{ p.businessMode }}</td><td>{{ p.spaceTemplateName || p.templateName }}</td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('project ui more')
