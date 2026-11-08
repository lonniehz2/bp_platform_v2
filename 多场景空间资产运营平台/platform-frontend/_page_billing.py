import io
p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'")
s=s.replace("import { can } from '../permissions'","import { can } from '../permissions'\nimport Pager from '../components/Pager.vue'")
s=s.replace("const payments = ref([])","const payments = ref([])\nconst page = ref(1)")
s=s.replace("const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })","const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })\nconst pagedBills = computed(() => bills.value.slice((page.value - 1) * 10, page.value * 10))")
s=s.replace('<tr v-for="b in bills" :key="b.id">','<tr v-for="b in pagedBills" :key="b.id">')
s=s.replace('''          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>收款记录</h2>''','''          </table>
        </div>
        <Pager :total="bills.length" :page="page" @update:page="page = $event" />
      </div>

      <div class="panel">
        <div class="panel-head"><h2>收款记录</h2>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('billing pager')
