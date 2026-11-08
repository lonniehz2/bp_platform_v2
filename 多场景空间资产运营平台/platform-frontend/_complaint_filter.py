import io
p=r'src\pages\Complaints.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'\nimport { useRoute } from 'vue-router'")
s=s.replace("const project = ref(null)","const route = useRoute()\nconst forcedType = computed(() => route.meta?.complaintType || '')\nconst pageTitle = computed(() => ({ APPEAL: '申诉管理', VISIT: '入户走访' }[forcedType.value] || '投诉与申诉'))\nconst visibleRecords = computed(() => forcedType.value ? records.value.filter(r => r.complaintType === forcedType.value) : records.value)\nconst project = ref(null)")
s=s.replace("const form = reactive({ complaintType: 'COMPLAINT',","const form = reactive({ complaintType: forcedType.value || 'COMPLAINT',")
s=s.replace("v-for=\"r in records\"","v-for=\"r in visibleRecords\"")
s=s.replace('<div><h2>投诉与申诉</h2><p>{{ project?.orgName || \'未选择项目\' }} · 投诉、申诉、入户走访</p></div>','<div><h2>{{ pageTitle }}</h2><p>{{ project?.orgName || \'未选择项目\' }} · 投诉、申诉、入户走访</p></div>')
s=s.replace('<div class="field"><label>类型</label><select v-model="form.complaintType">','<div class="field" v-if="!forcedType"><label>类型</label><select v-model="form.complaintType">')
# On load set filter type
s=s.replace("    if (!form.personId && p.length) form.personId = p[0].id","    if (!form.personId && p.length) form.personId = p[0].id\n    if (forcedType.value) type.value = forcedType.value")
# watch route type
s=s.replace("onMounted(load)","watch(forcedType, v => { if (v) { type.value = v; form.complaintType = v; load() } })\nonMounted(load)")
s=s.replace("import { computed, onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref, watch } from 'vue'")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('complaint filter')
