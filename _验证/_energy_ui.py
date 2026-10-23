# -*- coding: utf-8 -*-
"""账单页新增「能耗分析」：月度用量/金额 + 楼栋汇总 + 房源 TOP。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src',
                 'views', 'Bills.vue')
s = io.open(V, encoding='utf-8').read()

if 'energyVisible' in s:
    print('已存在')
    raise SystemExit(0)

anchor = '<el-button type="primary" plain @click="openMeter" data-testid="meter-reading">抄表录入</el-button>'
if anchor not in s:
    raise SystemExit('未找到抄表录入按钮')
s = s.replace(anchor, anchor + '''
        <el-button plain @click="openEnergy" data-testid="bill-energy">能耗分析</el-button>''', 1)

dialog = '''
    <!-- 能耗分析 -->
    <el-dialog v-model="energyVisible" title="能耗分析" width="860px">
      <div style="margin-bottom:8px">
        <el-radio-group v-model="energyMonths" size="small" @change="loadEnergy">
          <el-radio-button :value="3">近 3 月</el-radio-button>
          <el-radio-button :value="6">近 6 月</el-radio-button>
          <el-radio-button :value="12">近 12 月</el-radio-button>
        </el-radio-group>
        <span class="muted" style="font-size:12px;margin-left:8px">
          用量 = 本次读数 − 上次读数（跨月衔接）；金额 = 用量 × 收费项单价
        </span>
      </div>
      <el-row :gutter="12">
        <el-col :span="12">
          <div style="font-weight:600;margin-bottom:6px">月度趋势</div>
          <el-table :data="energyMonths0" size="small" border max-height="240">
            <el-table-column prop="month" label="月份" width="100" />
            <el-table-column prop="reading" label="读数次数" width="90" />
            <el-table-column prop="usage" label="用量" />
            <el-table-column prop="amount" label="金额" />
          </el-table>
        </el-col>
        <el-col :span="12">
          <div style="font-weight:600;margin-bottom:6px">楼栋汇总</div>
          <el-table :data="energyBuildings" size="small" border max-height="240">
            <el-table-column prop="building" label="楼栋" />
            <el-table-column prop="usage" label="用量" width="120" />
          </el-table>
        </el-col>
      </el-row>
      <div style="font-weight:600;margin:12px 0 6px">用量 TOP 10 房源</div>
      <el-table :data="energyTop" size="small" border max-height="260">
        <el-table-column prop="houseCode" label="房源编号" width="150" />
        <el-table-column prop="houseName" label="房源名称" min-width="180" />
        <el-table-column prop="building" label="楼栋" width="110" />
        <el-table-column prop="usage" label="用量" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="energyVisible = false">关闭</el-button>
      </template>
    </el-dialog>
'''
i = s.rfind('</template>')
s = s[:i] + dialog + s[i:]

script = '''
/** 能耗分析 */
const energyVisible = ref(false)
const energyMonths = ref(6)
const energyMonths0 = ref([])
const energyBuildings = ref([])
const energyTop = ref([])

function openEnergy() {
  energyVisible.value = true
  loadEnergy()
}

async function loadEnergy() {
  try {
    const r = await financeApi.meterAnalytics(energyMonths.value)
    const months = (r && r.months) || []
    energyMonths0.value = months.map((m) => ({
      month: m.month, reading: m.readings, usage: m.usage, amount: m.amount
    }))
    energyBuildings.value = (r && r.byBuilding) || []
    energyTop.value = (r && r.topHouses) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载能耗数据失败')
  }
}
'''
a = s.find('onMounted(')
s = s[:a] + script + '\n' + s[a:]

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('Bills.vue：能耗分析已加')

# API 封装
M = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src',
                 'api', 'modules.js')
m = io.open(M, encoding='utf-8').read()
if 'meterAnalytics' not in m:
    m = m.replace("  meterList:",
                  "  meterAnalytics: (months) =>\n"
                  "    req.get('/fin/meter-readings/analytics', { params: { months } }),\n"
                  "  meterList:", 1)
    io.open(M, 'w', encoding='utf-8', newline='').write(m)
    print('financeApi：meterAnalytics 已加')
