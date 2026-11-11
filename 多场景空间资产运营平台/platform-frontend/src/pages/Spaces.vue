<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import TreeSelect from '../components/TreeSelect.vue'
import { can } from '../permissions'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'
import { currentScene } from '../scene'

const { t } = useI18n()
const project = ref(null)
const spaces = ref([])
const assetTypes = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ parentId: '', spaceCode: '', spaceName: '', spaceType: 'BUILDING', assetTypeCode: 'PUBLIC_RENTAL' })
const types = ['AREA', 'BUILDING', 'UNIT', 'FLOOR', 'ROOM', 'INNER_ROOM', 'BED']
const editingSpace = ref(null)
const spaceEditForm = reactive({ spaceName: '', spaceType: 'ROOM', assetTypeCode: '', area: 0, innerArea: 0, rentable: false })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const [s, t] = await Promise.all([api.spaces(project.value.id), api.assetTypes(currentScene())])
    spaces.value = s; assetTypes.value = t
    if (!form.assetTypeCode && t.length) form.assetTypeCode = t[0].typeCode
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.spaceCode.trim() || !form.spaceName.trim()) throw new Error(t('spaces.required'))
    await api.createSpace(project.value.id, {
      parentId: form.parentId || null, spaceCode: form.spaceCode.trim(), spaceName: form.spaceName.trim(),
      spaceType: form.spaceType, assetTypeCode: form.assetTypeCode,
      rentable: ['ROOM', 'INNER_ROOM', 'BED'].includes(form.spaceType), area: 0, subUnitMode: null
    })
    form.spaceCode = ''; form.spaceName = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openSpaceEdit(s) {
  editingSpace.value = s
  Object.assign(spaceEditForm, {
    spaceName: s.spaceName || '', spaceType: s.spaceType || 'ROOM', assetTypeCode: s.assetTypeCode || '',
    area: s.area || 0, innerArea: s.innerArea || 0, rentable: !!s.rentable
  })
}


async function archiveSpace(s) {
  if (!await confirmAction({ title: t('spaces.archiveTitle'), message: t('spaces.archiveMessage', { name: s.spaceName }), confirmText: t('spaces.archiveConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archiveSpace(project.value.id, s.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function saveSpaceEdit() {
  busy.value = true; error.value = ''
  try {
    if (!spaceEditForm.spaceName.trim()) throw new Error(t('spaces.nameRequired'))
    await api.updateSpace(project.value.id, editingSpace.value.id, { ...spaceEditForm })
    editingSpace.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('spaces.title') }}</h2><p>{{ project?.orgName || t('spaces.noProject') }} · {{ t('spaces.subtitle') }}</p></div><span class="badge blue">{{ spaces.length }} {{ t('spaces.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('spaces.parent') }}</label><TreeSelect v-model="form.parentId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" :placeholder="t('spaces.selectParent')" clearable /></div>
        <div class="field"><label>{{ t('spaces.code') }}</label><input v-model="form.spaceCode" /></div>
        <div class="field"><label>{{ t('spaces.name') }}</label><input v-model="form.spaceName" /></div>
        <div class="field"><label>{{ t('spaces.type') }}</label><select v-model="form.spaceType"><option v-for="t in types" :key="t" :value="t">{{ enumLabel(t) }}</option></select></div>
        <div class="field"><label>{{ t('spaces.assetType') }}</label><select v-model="form.assetTypeCode"><option v-for="t in assetTypes" :key="t.typeCode" :value="t.typeCode">{{ t.typeName }}</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">{{ t('spaces.add') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('spaces.list') }}</h2><span class="small muted">{{ t('spaces.listHint') }}</span></div>
      <div v-if="!spaces.length" class="empty">{{ t('spaces.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('spaces.code') }}</th><th>{{ t('spaces.name') }}</th><th>{{ t('spaces.type') }}</th><th>{{ t('spaces.level') }}</th><th>{{ t('spaces.assetType') }}</th><th>{{ t('spaces.path') }}</th><th>{{ t('spaces.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="s in spaces" :key="s.id">
              <td class="mono">{{ s.spaceCode }}</td><td>{{ s.spaceName }}</td><td>{{ enumLabel(s.spaceType) }}</td>
              <td>{{ s.levelNo }}</td><td>{{ s.assetTypeCode ? enumLabel(s.assetTypeCode) : '-' }}</td><td class="small">{{ s.spacePath }}</td>
              <td><button class="sm" @click="openSpaceEdit(s)">{{ t('spaces.edit') }}</button> <button class="sm danger" :disabled="busy" @click="archiveSpace(s)">{{ t('spaces.archive') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="editingSpace" class="modal-mask" @click.self="editingSpace = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('spaces.editTitle') }}</h2><button class="sm" @click="editingSpace = null">{{ t('spaces.close') }}</button></div>
        <div class="field"><label>{{ t('spaces.code') }}</label><input :value="editingSpace.spaceCode" disabled /></div>
        <div class="field"><label>{{ t('spaces.name') }}</label><input v-model="spaceEditForm.spaceName" /></div>
        <div class="field"><label>{{ t('spaces.spaceType') }}</label><select v-model="spaceEditForm.spaceType"><option v-for="t in types" :key="t" :value="t">{{ enumLabel(t) }}</option></select></div>
        <div class="field"><label>{{ t('spaces.assetType') }}</label><input v-model="spaceEditForm.assetTypeCode" /></div>
        <div class="field"><label>{{ t('spaces.area') }}</label><input v-model.number="spaceEditForm.area" type="number" /></div>
        <div class="field"><label>{{ t('spaces.innerArea') }}</label><input v-model.number="spaceEditForm.innerArea" type="number" /></div>
        <div class="field"><label><input type="checkbox" v-model="spaceEditForm.rentable" /> {{ t('spaces.rentable') }}</label></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveSpaceEdit">{{ t('spaces.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
