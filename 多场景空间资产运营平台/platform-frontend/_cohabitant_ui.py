import io
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const files = ref([])","const files = ref([])\nconst cohabitants = ref([])\nconst cohabForm = reactive({ personId: '', relationType: 'FAMILY', startDate: '', endDate: '', remark: '' })")
s=s.replace("  files.value = await api.files('CONTRACT', c.id)","  files.value = await api.files('CONTRACT', c.id)\n  cohabitants.value = await api.cohabitants(c.id)\n  if (!cohabForm.personId && persons.value.length) cohabForm.personId = persons.value[0].id")
s=s.replace("async function downloadFile(f) {","async function addCohabitant() {\n  if (!selectedContract.value || !cohabForm.personId) { error.value = '请选择人员'; return }\n  busy.value = true; error.value = ''\n  try {\n    await api.addCohabitant(selectedContract.value.id, {\n      personId: cohabForm.personId, relationType: cohabForm.relationType,\n      startDate: cohabForm.startDate || null, endDate: cohabForm.endDate || null, remark: cohabForm.remark\n    })\n    cohabitants.value = await api.cohabitants(selectedContract.value.id)\n    cohabForm.remark = ''\n  } catch (e) { error.value = e.message } finally { busy.value = false }\n}\n\nasync function removeCohabitant(c) {\n  busy.value = true; error.value = ''\n  try { await api.removeCohabitant(c.id); cohabitants.value = await api.cohabitants(selectedContract.value.id) } catch (e) { error.value = e.message } finally { busy.value = false }\n}\n\nasync function downloadFile(f) {")
s=s.replace('''        <div v-for="f in files" :key="f.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ f.fileName }}</div><div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div>
          <button class="sm" @click="downloadFile(f)">下载</button>
        </div>
      </div>''','''        <div v-for="f in files" :key="f.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ f.fileName }}</div><div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div>
          <button class="sm" @click="downloadFile(f)">下载</button>
        </div>
      </div>

      <div v-if="selectedContract" class="panel">
        <div class="panel-head"><h2>合同同住人</h2><span class="small muted">{{ selectedContract.contractNo }} · {{ cohabitants.length }} 人</span></div>
        <div class="row" style="margin-bottom:10px">
          <div class="field" style="flex:2"><label>人员</label><select v-model="cohabForm.personId"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}（{{ p.personCode }}）</option></select></div>
          <div class="field"><label>关系</label><select v-model="cohabForm.relationType"><option value="SPOUSE">配偶</option><option value="CHILD">子女</option><option value="PARENT">父母</option><option value="FAMILY">家庭成员</option><option value="OTHER">其他</option></select></div>
          <div class="field"><label>开始</label><input v-model="cohabForm.startDate" type="date" /></div>
          <div class="field"><label>结束</label><input v-model="cohabForm.endDate" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addCohabitant">新增同住人</button></div>
        </div>
        <div v-if="!cohabitants.length" class="empty">暂无同住人</div>
        <div v-for="c in cohabitants" :key="c.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ c.personName }} · {{ c.relationType }}</div><div class="small muted">{{ c.validStart || c.startDate || '' }} ~ {{ c.endDate || '长期' }}</div></div>
          <span class="badge green">{{ c.cohabitantStatus }}</span>
          <button class="sm danger" :disabled="busy" @click="removeCohabitant(c)">移除</button>
        </div>
      </div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('cohabitant ui')
