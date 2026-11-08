import io
p=r'src\pages\Devices.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'")
s=s.replace("import { can } from '../permissions'","import { can } from '../permissions'\nimport Pager from '../components/Pager.vue'")
s=s.replace("const devices = ref([])","const devices = ref([])\nconst page = ref(1)")
s=s.replace("const money = (v) => Number(v || 0).toLocaleString('zh-CN')","const money = (v) => Number(v || 0).toLocaleString('zh-CN')\nconst pagedDevices = computed(() => devices.value.slice((page.value - 1) * 10, page.value * 10))")
s=s.replace('<tr v-for="d in devices" :key="d.id">','<tr v-for="d in pagedDevices" :key="d.id">')
s=s.replace('''          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>人员授权</h2>''','''          </table>
        </div>
        <Pager :total="devices.length" :page="page" @update:page="page = $event" />
      </div>

      <div class="panel">
        <div class="panel-head"><h2>人员授权</h2>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('devices pager')
