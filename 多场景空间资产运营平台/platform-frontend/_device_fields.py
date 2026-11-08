import io
p=r'src\pages\Devices.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const form = reactive({ deviceCode: '', deviceName: '', deviceType: 'LOCK', spaceId: '' })","const form = reactive({ deviceCode: '', deviceName: '', deviceType: 'LOCK', spaceId: '', deviceModel: '', installTime: '', warrantyEnd: '' })")
s=s.replace("      deviceType: form.deviceType, assetStatus: 'ACTIVE', businessStatus: 'IN_USE'","      deviceType: form.deviceType, deviceModel: form.deviceModel, installTime: form.installTime || null,\n      warrantyEnd: form.warrantyEnd || null, assetStatus: 'ACTIVE', businessStatus: 'IN_USE'")
s=s.replace('''          <div class="field"><label>绑定空间</label>''','''          <div class="field"><label>设备型号</label><input v-model="form.deviceModel" /></div>
          <div class="field"><label>安装时间</label><input v-model="form.installTime" type="datetime-local" /></div>
          <div class="field"><label>保修到期</label><input v-model="form.warrantyEnd" type="date" /></div>
          <div class="field"><label>绑定空间</label>''')
s=s.replace('''            <thead><tr><th>设备编码</th><th>名称</th><th>类型</th><th>绑定空间</th><th>资产状态</th><th>业务状态</th></tr></thead>''','''            <thead><tr><th>设备编码</th><th>名称</th><th>类型</th><th>型号</th><th>绑定空间</th><th>保修到期</th><th>资产状态</th><th>业务状态</th></tr></thead>''')
s=s.replace('''                <td class="mono">{{ d.deviceCode }}</td><td>{{ d.deviceName }}</td><td>{{ d.deviceType }}</td>
                <td>{{ d.spaceName || '-' }}</td><td><span class="badge green">{{ d.assetStatus }}</span></td><td>{{ d.businessStatus }}</td>''','''                <td class="mono">{{ d.deviceCode }}</td><td>{{ d.deviceName }}</td><td>{{ d.deviceType }}</td>
                <td>{{ d.deviceModel || '-' }}</td><td>{{ d.spaceName || '-' }}</td><td>{{ d.warrantyEnd || '-' }}</td>
                <td><span class="badge green">{{ d.assetStatus }}</span></td><td>{{ d.businessStatus }}</td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('device fields')
