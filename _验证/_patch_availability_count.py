# -*- coding: utf-8 -*-
"""补：短租可用性查询 + 换房次数列。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------------- 短租：可用性 ----------------
p = os.path.join(VIEWS, 'ShortRent.vue')
s = io.open(p, encoding='utf-8').read()
if 'checkAvailability' not in s:
    s = s.replace('''        <el-button type="primary" :loading="bhLoading" @click="loadByHouse">查询</el-button>
      </div>''', '''        <el-button type="primary" :loading="bhLoading" @click="loadByHouse">查询</el-button>
      </div>

      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <span class="muted" style="font-size:12px">可用性（按日期段）</span>
        <el-date-picker v-model="bh.checkIn" type="date" value-format="YYYY-MM-DD"
                        placeholder="入住" style="width:140px" />
        <el-date-picker v-model="bh.checkOut" type="date" value-format="YYYY-MM-DD"
                        placeholder="退房" style="width:140px" />
        <el-button plain :loading="avLoading" @click="checkAvailability">查可用性</el-button>
      </div>
      <el-alert v-if="av" :type="av.available ? 'success' : 'warning'" :closable="false"
                :title="(av.houseName || av.houseCode || '房源') + '：' + (av.available ? '可整段出租' : '不可整段出租')
                  + '（' + av.freeDays + '/' + av.days + ' 天可售）'"
                style="margin-bottom:10px" />''', 1)

    if 'const av = ref' not in s:
        s = s.replace('''const bhRows = ref([])''', '''const bhRows = ref([])
const av = ref(null)
const avLoading = ref(false)''', 1)
        s = s.replace('''const bh = reactive({ houseId: '', date: new Date().toISOString().slice(0, 10) })''',
                      '''const bh = reactive({ houseId: '', date: new Date().toISOString().slice(0, 10),
  checkIn: '', checkOut: '' })''', 1)
        s = s.replace('''async function loadByHouse() {''', '''async function checkAvailability() {
  if (!bh.houseId) { ElMessage.warning('请选择房源'); return }
  if (!bh.checkIn || !bh.checkOut) { ElMessage.warning('请选择入住与退房日期'); return }
  avLoading.value = true
  try {
    av.value = await req.get('/house-calendar/' + bh.houseId + '/availability',
      { params: { checkIn: bh.checkIn, checkOut: bh.checkOut } })
  } catch (e) {
    av.value = null
    ElMessage.error(e?.response?.data?.message || '查询失败')
  } finally { avLoading.value = false }
}

async function loadByHouse() {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('短租可用性已加')

# ---------------- 换房：已换次数 ----------------
p = os.path.join(VIEWS, 'Exchanges.vue')
s = io.open(p, encoding='utf-8').read()
if 'exchangeTimes' not in s:
    s = s.replace('''      <el-table-column prop="exchangeStatus" label="状态"''',
                  '''      <el-table-column prop="exchangeTimes" label="已换次数" width="100" />
      <el-table-column prop="exchangeStatus" label="状态"''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('换房次数列已加')
