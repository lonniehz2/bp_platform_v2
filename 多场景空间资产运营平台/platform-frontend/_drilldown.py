import io
p=r'src\pages\Dashboard.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'","import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'\nimport { useRouter } from 'vue-router'")
s=s.replace("const loading = ref(true)","const router = useRouter()\nconst loading = ref(true)")
s=s.replace('''const periodMode = ref('month')''','''const periodMode = ref('month')''')
# insert function before colors
marker='''function colors() {'''
js='''function drillBilling() {
  if (!project.value) return
  localStorage.setItem('platformProjectId', project.value.id)
  router.push({ path: '/billing', query: {
    periodStart: periodRange.value.start,
    periodEnd: periodRange.value.end
  } })
}

function colors() {'''
s=s.replace(marker,js,1)
s=s.replace('''<div class="card"><div class="label">本期应收</div>''','''<div class="card clickable" @click="drillBilling"><div class="label">本期应收</div>''')
s=s.replace('''<div class="card"><div class="label">本期实收</div>''','''<div class="card clickable" @click="drillBilling"><div class="label">本期实收</div>''')
s=s.replace('''<div class="card"><div class="label">本期收缴率</div>''','''<div class="card clickable" @click="drillBilling"><div class="label">本期收缴率</div>''')
s=s.replace('''<div class="card"><div class="label">总欠费</div>''','''<div class="card clickable" @click="drillBilling"><div class="label">总欠费</div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const payments = ref([])","const payments = ref([])\nconst drillRange = ref({ start: '', end: '' })")
s=s.replace('''    const [b, p] = await Promise.all([api.bills(project.value.id), api.payments(project.value.id)])
    bills.value = b; payments.value = p''','''    const [b, p] = await Promise.all([api.bills(project.value.id), api.payments(project.value.id)])
    drillRange.value = { start: String(route.query.periodStart || ''), end: String(route.query.periodEnd || '') }
    bills.value = b.filter(x => {
      const d = String(x.periodStart || '').slice(0, 10)
      return (!drillRange.value.start || d >= drillRange.value.start)
        && (!drillRange.value.end || d <= drillRange.value.end)
    })
    payments.value = p''')
s=s.replace('''<div class="panel-head"><h2>账单列表</h2><span class="small muted">应收 {{ bills.length }} 笔</span></div>''','''<div class="panel-head"><h2>账单列表</h2><span class="small muted" v-if="drillRange.start">账期 {{ drillRange.start }} ~ {{ drillRange.end }} · 应收 {{ bills.length }} 笔</span><span class="small muted" v-else>应收 {{ bills.length }} 笔</span></div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('drilldown')
