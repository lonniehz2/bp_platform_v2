import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'updateHouse' not in s:
 s=s.replace("  createSpace: (projectId, body)","  updateHouse: (houseId, body) => request(`/houses/${houseId}/update`, { method: 'POST', body: JSON.stringify(body) }),\n  createSpace: (projectId, body)")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Houses.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { computed, onMounted, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'")
s=s.replace("const error = ref('')","const error = ref('')\nconst editing = ref(null)\nconst editForm = reactive({ area: 0, innerArea: 0, houseStatus: 'VACANT', assetTypeCode: '' })")
s=s.replace("onMounted(load)","function openEdit(h) {\n  editing.value = h\n  editForm.area = h.area || 0; editForm.innerArea = h.innerArea || 0\n  editForm.houseStatus = h.houseStatus || 'VACANT'; editForm.assetTypeCode = h.assetTypeCode || ''\n}\n\nasync function saveEdit() {\n  try {\n    await api.updateHouse(editing.value.id, { ...editForm })\n    editing.value = null\n    await load()\n  } catch (e) { error.value = e.message }\n}\n\nonMounted(load)")
s=s.replace('''            <thead><tr><th>房源编码</th><th>名称</th><th>资产类型</th><th>面积</th><th>房态</th></tr></thead>''','''            <thead><tr><th>房源编码</th><th>名称</th><th>资产类型</th><th>建筑面积</th><th>套内面积</th><th>房态</th><th>操作</th></tr></thead>''')
s=s.replace('''              <td>{{ h.assetTypeCode || '-' }}</td><td>{{ h.area || '-' }}</td>
              <td><span class="badge" :class="h.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ h.houseStatus }}</span></td>''','''              <td>{{ h.assetTypeCode || '-' }}</td><td>{{ h.area || '-' }}</td><td>{{ h.innerArea || '-' }}</td>
              <td><span class="badge" :class="h.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ h.houseStatus }}</span></td>
              <td><button class="sm" @click="openEdit(h)">编辑</button></td>''')
s=s.replace('''      <Pager :total="filtered.length" :page="page" @update:page="page = $event" />
    </div>
  </div>
</template>''','''      <Pager :total="filtered.length" :page="page" @update:page="page = $event" />
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑房源</h2><button class="sm" @click="editing = null">关闭</button></div>
        <div class="field"><label>房源</label><div class="mono">{{ editing.houseCode }} · {{ editing.houseName }}</div></div>
        <div class="row">
          <div class="field"><label>建筑面积</label><input v-model.number="editForm.area" type="number" /></div>
          <div class="field"><label>套内面积</label><input v-model.number="editForm.innerArea" type="number" /></div>
          <div class="field"><label>房态</label><select v-model="editForm.houseStatus"><option value="VACANT">空置</option><option value="ALLOCATED">已配租</option><option value="OCCUPIED">已入住</option><option value="FROZEN">冻结</option></select></div>
          <div class="field"><label>资产类型</label><input v-model="editForm.assetTypeCode" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" @click="saveEdit">保存</button></div>
      </div>
    </div>
  </div>
</template>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('house ui')
