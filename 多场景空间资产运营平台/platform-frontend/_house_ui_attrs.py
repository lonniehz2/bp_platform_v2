import io
p=r'src\pages\Houses.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const editForm = reactive({ area: 0, innerArea: 0, houseStatus: 'VACANT', assetTypeCode: '' })","const editForm = reactive({ area: 0, innerArea: 0, houseStatus: 'VACANT', assetTypeCode: '', layoutType: '', orientation: '', floorNo: 1, totalFloors: 1 })")
s=s.replace("  editForm.houseStatus = h.houseStatus || 'VACANT'; editForm.assetTypeCode = h.assetTypeCode || ''","  editForm.houseStatus = h.houseStatus || 'VACANT'; editForm.assetTypeCode = h.assetTypeCode || ''\n  editForm.layoutType = h.layoutType || ''; editForm.orientation = h.orientation || ''\n  editForm.floorNo = h.floorNo || 1; editForm.totalFloors = h.totalFloors || 1")
s=s.replace('''            <thead><tr><th>房源编码</th><th>名称</th><th>资产类型</th><th>建筑面积</th><th>套内面积</th><th>房态</th><th>操作</th></tr></thead>''','''            <thead><tr><th>房源编码</th><th>名称</th><th>户型</th><th>朝向</th><th>楼层</th><th>建筑面积</th><th>套内面积</th><th>房态</th><th>操作</th></tr></thead>''')
s=s.replace('''              <td>{{ h.assetTypeCode || '-' }}</td><td>{{ h.area || '-' }}</td><td>{{ h.innerArea || '-' }}</td>''','''              <td>{{ h.layoutType || '-' }}</td><td>{{ h.orientation || '-' }}</td><td>{{ h.floorNo || '-' }}/{{ h.totalFloors || '-' }}</td><td>{{ h.area || '-' }}</td><td>{{ h.innerArea || '-' }}</td>''')
s=s.replace('''          <div class="field"><label>资产类型</label><input v-model="editForm.assetTypeCode" /></div>''','''          <div class="field"><label>资产类型</label><input v-model="editForm.assetTypeCode" /></div>
          <div class="field"><label>户型</label><input v-model="editForm.layoutType" placeholder="如 二室一厅" /></div>
          <div class="field"><label>朝向</label><select v-model="editForm.orientation"><option value="">未填写</option><option value="SOUTH">南</option><option value="NORTH">北</option><option value="EAST">东</option><option value="WEST">西</option><option value="SOUTHEAST">东南</option><option value="SOUTHWEST">西南</option></select></div>
          <div class="field"><label>所在楼层</label><input v-model.number="editForm.floorNo" type="number" min="1" /></div>
          <div class="field"><label>总楼层</label><input v-model.number="editForm.totalFloors" type="number" min="1" /></div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('house ui attrs')
