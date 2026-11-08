import io
p=r'src\pages\Persons.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const grants = ref([])","const grants = ref([])\nconst relations = ref([])\nconst projects = ref([])\nconst houses = ref([])\nconst project = ref(null)")
s=s.replace("const form = reactive({ personCode:","const relForm = reactive({ targetType: 'HOUSE', targetId: '', relationType: 'TENANT', startDate: '', endDate: '' })\nconst form = reactive({ personCode:")
s=s.replace("    try { persons.value = await api.persons() } catch (e) { error.value = e.message }","    persons.value = await api.persons()\n    projects.value = await api.projects()\n    const saved = String(localStorage.getItem('platformProjectId') || '')\n    project.value = projects.value.find(p => String(p.id) === saved) || projects.value[0] || null\n    if (project.value) houses.value = await api.houses(project.value.id)\n    if (!relForm.targetId && houses.value.length) relForm.targetId = houses.value[0].id\n  } catch (e) { error.value = e.message }")
s=s.replace("  try { grants.value = await api.keyring(p.id) } catch { grants.value = [] }","  try { grants.value = await api.keyring(p.id); relations.value = await api.relations(p.id) } catch { grants.value = []; relations.value = [] }")
s=s.replace("onMounted(load)","async function addRelation() {\n  if (!selected.value || !relForm.targetId) { error.value = '请选择关联对象'; return }\n  busy.value = true; error.value = ''\n  try {\n    await api.createRelation(selected.value.id, {\n      projectId: project.value?.id, targetType: relForm.targetType, targetId: relForm.targetId,\n      relationType: relForm.relationType, startDate: relForm.startDate || null, endDate: relForm.endDate || null\n    })\n    relations.value = await api.relations(selected.value.id)\n  } catch (e) { error.value = e.message } finally { busy.value = false }\n}\n\nonMounted(load)")
# add relations panel after keyring panel before closing grid
s=s.replace('''        <div v-for="g in grants" :key="g.id" class="row" style="padding:9px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1">
            <div>{{ g.targetName || g.targetType }}</div>
            <div class="small muted">{{ g.targetType }} · {{ g.validStart }} ~ {{ g.validEnd || '长期' }}</div>
          </div>
          <span class="badge blue">{{ g.grantLevel }}</span>
        </div>
      </div>
    </div>''','''        <div v-for="g in grants" :key="g.id" class="row" style="padding:9px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1">
            <div>{{ g.targetName || g.targetType }}</div>
            <div class="small muted">{{ g.targetType }} · {{ g.validStart }} ~ {{ g.validEnd || '长期' }}</div>
          </div>
          <span class="badge blue">{{ g.grantLevel }}</span>
        </div>
      </div>
    </div>

    <div v-if="selected" class="panel">
      <div class="panel-head"><div><h2>人员关系</h2><p>{{ selected.personName }} · 项目/房屋/空间关系</p></div><span class="small muted">{{ relations.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="relForm.targetType"><option value="HOUSE">房屋</option><option value="PROJECT">项目</option></select></div>
        <div class="field" style="flex:2"><label>关联对象</label><select v-model="relForm.targetId"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
        <div class="field"><label>关系</label><select v-model="relForm.relationType"><option value="TENANT">承租人</option><option value="FAMILY">家庭成员</option><option value="COHABITANT">同住人</option><option value="OWNER">产权人</option></select></div>
        <div class="field"><label>开始</label><input v-model="relForm.startDate" type="date" /></div>
        <div class="field"><label>结束</label><input v-model="relForm.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addRelation">新增关系</button></div>
      </div>
      <div v-if="!relations.length" class="empty">暂无关系</div>
      <div v-for="r in relations" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
        <div style="flex:1"><div>{{ r.targetName }} · {{ r.relationType }}</div><div class="small muted">{{ r.startDate || '' }} ~ {{ r.endDate || '长期' }}</div></div>
        <span class="badge green">{{ r.status }}</span>
      </div>
    </div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('relations ui')
