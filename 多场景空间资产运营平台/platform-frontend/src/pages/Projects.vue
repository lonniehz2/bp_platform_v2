<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import TreeSelect from '../components/TreeSelect.vue'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'
import { currentScene } from '../scene'

const { t } = useI18n()
const projects = ref([])
const templates = ref([])
const modes = ref([])
const spaces = ref([])
const houses = ref([])
const assetTypes = ref([])
const currentProject = ref(null)
const page = ref(1)
const error = ref('')
const busy = ref(false)
const pagedProjects = computed(() => projects.value.slice((page.value - 1) * 10, page.value * 10))
const form = reactive({ orgCode: '', orgName: t('proj.defaultName'), businessMode: 'PUBLIC_RENTAL', spaceTemplateId: '', defaultAssetTypeCode: 'PUBLIC_RENTAL', address: '', contactName: '', contactPhone: '', remark: '', totalArea: 0, landArea: 0, propertyType: '', buildYear: 2020 })
const editingProject = ref(null)
const projectEditForm = reactive({ orgName: '', address: '', contactName: '', contactPhone: '', remark: '', totalArea: 0, landArea: 0, propertyType: '', buildYear: 2020 })
const spaceForm = reactive({ parentId: '', spaceCode: '', spaceName: '', spaceType: 'BUILDING', assetTypeCode: 'PUBLIC_RENTAL', rentable: false, area: 0 })
const spaceTypes = ['AREA', 'BUILDING', 'UNIT', 'FLOOR', 'ROOM', 'INNER_ROOM', 'BED']

async function load() {
  try {
    const [p, t, m, at] = await Promise.all([
      api.projects(), api.templates(currentScene()), api.modes(currentScene()), api.assetTypes(currentScene())
    ])
    projects.value = p
    templates.value = t
    modes.value = m
    assetTypes.value = at
    if (!form.spaceTemplateId && t.length) form.spaceTemplateId = t[0].id
    const saved = String(localStorage.getItem('platformProjectId') || '')
    const chosen = projects.value.find(x => String(x.id) === saved) || projects.value[0]
    if (chosen) await selectProject(chosen)
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.orgCode.trim()) throw new Error(t('proj.requiredCode'))
    if (!form.orgName.trim()) throw new Error(t('proj.requiredName'))
    if (form.contactPhone && !/^1\d{10}$/.test(form.contactPhone)) throw new Error(t('proj.invalidPhone'))
    if (Number(form.totalArea) < 0 || Number(form.landArea) < 0) throw new Error(t('proj.negativeArea'))
    if (form.buildYear && (form.buildYear < 1900 || form.buildYear > 2100)) throw new Error(t('proj.invalidYear'))
    await api.createProject({
      orgCode: form.orgCode.trim(), orgName: form.orgName.trim(),
      sceneCode: currentScene(), businessMode: form.businessMode,
      spaceTemplateId: form.spaceTemplateId,
      defaultAssetTypeCode: form.defaultAssetTypeCode,
      address: form.address, contactName: form.contactName,
      contactPhone: form.contactPhone, remark: form.remark,
      totalArea: Number(form.totalArea || 0), landArea: Number(form.landArea || 0),
      propertyType: form.propertyType, buildYear: Number(form.buildYear || 0)
    })
    form.orgCode = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openProjectEdit(p) {
  editingProject.value = p
  Object.assign(projectEditForm, {
    orgName: p.orgName || '', address: p.address || '', contactName: p.contactName || '',
    contactPhone: p.contactPhone || '', remark: p.remark || '', totalArea: p.totalArea || 0,
    landArea: p.landArea || 0, propertyType: p.propertyType || '', buildYear: p.buildYear || 2020
  })
}


async function archiveProject(p) {
  if (!await confirmAction({ title: t('proj.archiveTitle'), message: t('proj.archiveMessage', { name: p.orgName }), confirmText: t('proj.archiveConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archiveProject(p.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function saveProjectEdit() {
  busy.value = true; error.value = ''
  try {
    if (!projectEditForm.orgName.trim()) throw new Error(t('proj.nameRequired'))
    await api.updateProject(editingProject.value.id, { ...projectEditForm })
    editingProject.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function selectProject(p) {
  currentProject.value = p
  localStorage.setItem('platformProjectId', p.id)
  spaceForm.parentId = ''
  await loadAssets()
}

async function loadAssets() {
  if (!currentProject.value) return
  try {
    const id = currentProject.value.id
    const [s, h] = await Promise.all([api.spaces(id), api.houses(id)])
    spaces.value = s; houses.value = h
  } catch (e) { error.value = e.message }
}

async function createSpace() {
  busy.value = true; error.value = ''
  try {
    if (!spaceForm.spaceCode.trim() || !spaceForm.spaceName.trim()) throw new Error(t('proj.requiredSpace'))
    await api.createSpace(currentProject.value.id, {
      parentId: spaceForm.parentId || null,
      spaceCode: spaceForm.spaceCode.trim(),
      spaceName: spaceForm.spaceName.trim(),
      spaceType: spaceForm.spaceType,
      assetTypeCode: spaceForm.assetTypeCode,
      rentable: spaceForm.spaceType === 'ROOM' || spaceForm.spaceType === 'INNER_ROOM' || spaceForm.spaceType === 'BED'
        ? spaceForm.rentable : false,
      area: Number(spaceForm.area || 0),
      subUnitMode: null
    })
    spaceForm.spaceCode = ''; spaceForm.spaceName = ''
    await loadAssets()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="panel">
      <div class="panel-head">
        <div><h2>{{ t('proj.title') }}</h2><p>{{ t('proj.subtitle') }}</p></div>
        <span class="badge blue">{{ currentScene() }}</span>
      </div>
      <div class="row">
        <div class="field"><label>{{ t('proj.code') }}</label><input v-model="form.orgCode" :placeholder="t('proj.placeholderCode')" /></div>
        <div class="field"><label>{{ t('proj.name') }}</label><input v-model="form.orgName" /></div>
        <div class="field"><label>{{ t('proj.mode') }}</label>
          <select v-model="form.businessMode"><option v-for="m in modes" :key="m.modeCode" :value="m.modeCode">{{ m.modeName }}</option></select>
        </div>
        <div class="field"><label>{{ t('proj.template') }}</label>
          <select v-model="form.spaceTemplateId"><option v-for="t in templates" :key="t.id" :value="t.id">{{ t.templateName }}</option></select>
        </div>
        <div class="field" style="flex:2"><label>{{ t('proj.address') }}</label><input v-model="form.address" /></div>
        <div class="field"><label>{{ t('proj.contact') }}</label><input v-model="form.contactName" /></div>
        <div class="field"><label>{{ t('proj.phone') }}</label><input v-model="form.contactPhone" /></div>
        <div class="field"><label>{{ t('proj.totalArea') }}</label><input v-model.number="form.totalArea" type="number" /></div>
        <div class="field"><label>{{ t('proj.landArea') }}</label><input v-model.number="form.landArea" type="number" /></div>
        <div class="field"><label>{{ t('proj.property') }}</label><select v-model="form.propertyType"><option value="">{{ t('proj.unset') }}</option><option value="STATE">{{ t('proj.state') }}</option><option value="COLLECTIVE">{{ t('proj.collective') }}</option><option value="PRIVATE">{{ t('proj.private') }}</option></select></div>
        <div class="field"><label>{{ t('proj.buildYear') }}</label><input v-model.number="form.buildYear" type="number" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">{{ t('proj.create') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('proj.list') }}</h2><span class="small muted">{{ t('proj.listHint') }}</span></div>
      <div v-if="!projects.length" class="empty">{{ t('proj.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('proj.code') }}</th><th>{{ t('proj.name') }}</th><th>{{ t('proj.addressCol') }}</th><th>{{ t('proj.contact') }}</th><th>{{ t('proj.totalArea') }}</th><th>{{ t('proj.property') }}</th><th>{{ t('proj.mode') }}</th><th>{{ t('proj.templateCol') }}</th><th>{{ t('proj.status') }}</th><th>{{ t('proj.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="p in pagedProjects" :key="p.id" :class="{ active: currentProject && String(currentProject.id) === String(p.id) }">
              <td class="mono">{{ p.orgCode }}</td><td>{{ p.orgName }}</td><td>{{ p.address || '-' }}</td>
              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.totalArea || '-' }}</td>
              <td>{{ enumLabel(p.propertyType || '-') }}</td><td>{{ enumLabel(p.businessMode) }}</td>
              <td>{{ p.templateName || p.spaceTemplateId }}</td>
              <td><span class="badge green">{{ p.status }}</span></td>
              <td><button class="sm" @click="selectProject(p)">{{ t('proj.setCurrent') }}</button> <button class="sm" @click="openProjectEdit(p)">{{ t('proj.edit') }}</button> <button class="sm danger" :disabled="busy" @click="archiveProject(p)">{{ t('proj.archive') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="projects.length" :page="page" @update:page="page = $event" />
    </div>

    <template v-if="currentProject">
      <div class="panel">
        <div class="panel-head">
          <div><h2>{{ t('proj.spaceTree') }}</h2><p>{{ currentProject.orgName }} · {{ t('proj.spaceTreeHint') }}</p></div>
          <span class="small muted">{{ spaces.length }} {{ t('proj.spaces') }} · {{ houses.length }} {{ t('proj.houses') }}</span>
        </div>
        <div class="row" style="margin-bottom:12px">
          <div class="field"><label>{{ t('proj.parent') }}</label>
            <TreeSelect v-model="spaceForm.parentId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" :placeholder="t('proj.placeholderParent')" clearable />
          </div>
          <div class="field"><label>{{ t('proj.spaceCode') }}</label><input v-model="spaceForm.spaceCode" :placeholder="t('proj.placeholderSpaceCode')" /></div>
          <div class="field"><label>{{ t('proj.spaceName') }}</label><input v-model="spaceForm.spaceName" :placeholder="t('proj.placeholderSpaceName')" /></div>
          <div class="field"><label>{{ t('proj.type') }}</label>
            <select v-model="spaceForm.spaceType"><option v-for="t in spaceTypes" :key="t" :value="t">{{ t }}</option></select>
          </div>
          <div class="field"><label>{{ t('proj.assetType') }}</label>
            <select v-model="spaceForm.assetTypeCode"><option v-for="t in assetTypes" :key="t.typeCode" :value="t.typeCode">{{ t.typeName }}</option></select>
          </div>
          <div class="field" v-if="['ROOM','INNER_ROOM','BED'].includes(spaceForm.spaceType)" style="flex:0 0 auto">
            <label>{{ t('proj.rentable') }}</label><input v-model="spaceForm.rentable" type="checkbox" style="width:auto" />
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="createSpace">{{ t('proj.addSpace') }}</button></div>
        </div>
        <div v-if="!spaces.length" class="empty">{{ t('proj.noSpaces') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('proj.spaceCode') }}</th><th>{{ t('proj.nameCol2') }}</th><th>{{ t('proj.type') }}</th><th>{{ t('proj.level') }}</th><th>{{ t('proj.assetType') }}</th><th>{{ t('proj.path') }}</th></tr></thead>
            <tbody>
              <tr v-for="s in spaces" :key="s.id">
                <td class="mono">{{ s.spaceCode }}</td><td>{{ s.spaceName }}</td><td>{{ enumLabel(s.spaceType) }}</td>
                <td>{{ s.levelNo }}</td><td>{{ s.assetTypeCode || '-' }}</td><td class="small">{{ s.spacePath }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('proj.houseTitle') }}</h2><span class="small muted">{{ t('proj.houseHint') }}</span></div>
        <div v-if="!houses.length" class="empty">{{ t('proj.noHouses') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('proj.houseCode') }}</th><th>{{ t('proj.nameCol2') }}</th><th>{{ t('proj.assetType') }}</th><th>{{ t('proj.area') }}</th><th>{{ t('proj.status') }}</th></tr></thead>
            <tbody>
              <tr v-for="h in houses" :key="h.id">
                <td class="mono">{{ h.houseCode }}</td><td>{{ h.houseName }}</td>
                <td>{{ h.assetTypeCode || '-' }}</td><td>{{ h.area || '-' }}</td>
                <td><span class="badge" :class="h.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ enumLabel(h.houseStatus) }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-if="editingProject" class="modal-mask" @click.self="editingProject = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('proj.editTitle') }}</h2><button class="sm" @click="editingProject = null">{{ t('proj.close') }}</button></div>
        <div class="field"><label>{{ t('proj.code') }}</label><input :value="editingProject.orgCode" disabled /></div>
        <div class="field"><label>{{ t('proj.name') }}</label><input v-model="projectEditForm.orgName" /></div>
        <div class="field"><label>{{ t('proj.addressCol') }}</label><input v-model="projectEditForm.address" /></div>
        <div class="field"><label>{{ t('proj.contact') }}</label><input v-model="projectEditForm.contactName" /></div>
        <div class="field"><label>{{ t('proj.phone') }}</label><input v-model="projectEditForm.contactPhone" /></div>
        <div class="field"><label>{{ t('proj.totalArea') }}</label><input v-model.number="projectEditForm.totalArea" type="number" /></div>
        <div class="field"><label>{{ t('proj.property') }}</label><input v-model="projectEditForm.propertyType" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveProjectEdit">{{ t('proj.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
