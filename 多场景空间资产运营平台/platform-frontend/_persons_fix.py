import io
p=r'src\pages\Persons.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''async function load() {
  error.value = ''
  try { persons.value = await api.persons() } catch (e) { error.value = e.message }
}''','''async function load() {
  error.value = ''
  try {
    const all = await api.projects()
    projects.value = all
    const saved = String(localStorage.getItem('platformProjectId') || '')
    project.value = all.find(p => String(p.id) === saved) || all[0] || null
    persons.value = await api.persons()
    houses.value = project.value ? await api.houses(project.value.id) : []
  } catch (e) { error.value = e.message }
}''')
s=s.replace('''<div class="field"><label>类型</label><select v-model="relForm.targetType"><option value="HOUSE">房屋</option><option value="PROJECT">项目</option></select></div>
        <div class="field" style="flex:2"><label>关联对象</label><select v-model="relForm.targetId"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>''','''<div class="field"><label>类型</label><select v-model="relForm.targetType" @change="relForm.targetId = ''"><option value="HOUSE">房屋</option><option value="PROJECT">项目</option></select></div>
        <div class="field" style="flex:2"><label>关联对象</label>
          <select v-model="relForm.targetId">
            <template v-if="relForm.targetType === 'HOUSE'"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></template>
            <template v-else><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.orgName }}（{{ p.orgCode }}）</option></template>
          </select>
        </div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('persons fix')
