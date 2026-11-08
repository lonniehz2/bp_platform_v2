import io
p=r'src\pages\Projects.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const form = reactive({ orgCode: '', orgName: '保障房项目', businessMode: 'PUBLIC_RENTAL', spaceTemplateId: '', defaultAssetTypeCode: 'PUBLIC_RENTAL' })","const form = reactive({ orgCode: '', orgName: '保障房项目', businessMode: 'PUBLIC_RENTAL', spaceTemplateId: '', defaultAssetTypeCode: 'PUBLIC_RENTAL', address: '', contactName: '', contactPhone: '', remark: '' })")
s=s.replace("      defaultAssetTypeCode: form.defaultAssetTypeCode\n    })","      defaultAssetTypeCode: form.defaultAssetTypeCode,\n      address: form.address, contactName: form.contactName,\n      contactPhone: form.contactPhone, remark: form.remark\n    })")
s=s.replace('''        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">创建项目</button></div>''','''        <div class="field" style="flex:2"><label>项目地址</label><input v-model="form.address" /></div>
        <div class="field"><label>联系人</label><input v-model="form.contactName" /></div>
        <div class="field"><label>联系电话</label><input v-model="form.contactPhone" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">创建项目</button></div>''')
s=s.replace('''            <thead><tr><th>项目编码</th><th>项目名称</th><th>经营模式</th><th>模板</th><th>状态</th><th>操作</th></tr></thead>''','''            <thead><tr><th>项目编码</th><th>项目名称</th><th>地址</th><th>联系人</th><th>经营模式</th><th>模板</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''              <td class="mono">{{ p.orgCode }}</td><td>{{ p.orgName }}</td><td>{{ p.businessMode }}</td>''','''              <td class="mono">{{ p.orgCode }}</td><td>{{ p.orgName }}</td><td>{{ p.address || '-' }}</td>
              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.businessMode }}</td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('project ui')
