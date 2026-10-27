# -*- coding: utf-8 -*-
"""短租：按房源查订单 + 住晚计算；换房次数。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------------- 短租 ----------------
p = os.path.join(VIEWS, 'ShortRent.vue')
s = io.open(p, encoding='utf-8').read()
if 'byHouseVisible' not in s:
    s = s.replace('''      <el-button @click="resetQuery">清空</el-button>''',
                  '''      <el-button @click="resetQuery">清空</el-button>
      <el-button type="primary" plain @click="byHouseVisible = true">按房源查</el-button>
      <el-button plain @click="nightsVisible = true">住晚计算</el-button>''', 1)

    dialog = '''
    <!-- 按房源查当日订单 -->
    <el-dialog v-model="byHouseVisible" title="按房源查订单" width="760px">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <HouseSelect v-model="bh.houseId" width="260px" testid="sr-byhouse-house" />
        <el-date-picker v-model="bh.date" type="date" value-format="YYYY-MM-DD"
                        placeholder="日期" style="width:150px" />
        <el-button type="primary" :loading="bhLoading" @click="loadByHouse">查询</el-button>
      </div>
      <el-table :data="bhRows" size="small" border max-height="360">
        <el-table-column prop="orderNo" label="订单号" width="170" />
        <el-table-column prop="checkInTime" label="入住" width="150" />
        <el-table-column prop="checkOutTime" label="退房" width="150" />
        <el-table-column prop="orderStatusLabel" label="状态" width="110" />
        <el-table-column prop="totalAmount" label="金额" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="byHouseVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 住晚计算 -->
    <el-dialog v-model="nightsVisible" title="住晚计算" width="520px">
      <el-alert type="info" :closable="false" show-icon
                title="退房时刻必须晚于入住时刻；跨夜按自然夜计算。" />
      <el-form label-width="90px" style="margin-top:12px">
        <el-form-item label="入住">
          <el-date-picker v-model="ng.checkIn" type="datetime"
                          value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="退房">
          <el-date-picker v-model="ng.checkOut" type="datetime"
                          value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert v-if="ngNights !== null" :type="ngNights > 0 ? 'success' : 'error'"
                :closable="false" :title="ngNights > 0 ? ('共 ' + ngNights + ' 晚') : '退房时间不合法'" />
      <template #footer>
        <el-button @click="nightsVisible = false">关闭</el-button>
        <el-button type="primary" @click="calcNights">计算</el-button>
      </template>
    </el-dialog>
'''
    idx = s.rfind('</template>')
    s = s[:idx] + dialog + s[idx:]

    if 'const byHouseVisible' not in s:
        s = s.replace('''const formVisible = ref(false)''', '''const byHouseVisible = ref(false)
const bh = reactive({ houseId: '', date: new Date().toISOString().slice(0, 10) })
const bhRows = ref([])
const bhLoading = ref(false)
const nightsVisible = ref(false)
const ng = reactive({ checkIn: '', checkOut: '' })
const ngNights = ref(null)

async function loadByHouse() {
  if (!bh.houseId) { ElMessage.warning('请选择房源'); return }
  bhLoading.value = true
  try {
    const d = await req.get('/short-rent-orders/by-house',
      { params: { houseId: bh.houseId, date: bh.date, pageNum: 1, pageSize: 50 } })
    bhRows.value = d.rows || []
  } catch (e) {
    bhRows.value = []
    ElMessage.error(e?.response?.data?.message || '查询失败')
  } finally { bhLoading.value = false }
}

async function calcNights() {
  if (!ng.checkIn || !ng.checkOut) { ElMessage.warning('请选择入住与退房时间'); return }
  try {
    ngNights.value = await req.get('/short-rent-orders/calc-nights',
      { params: { checkIn: ng.checkIn, checkOut: ng.checkOut } })
  } catch (e) {
    ngNights.value = null
    ElMessage.error(e?.response?.data?.message || '计算失败')
  }
}

const formVisible = ref(false)''', 1)
    if "import HouseSelect" not in s:
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport HouseSelect from '@/components/HouseSelect.vue'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('短租两个小工具已加')
