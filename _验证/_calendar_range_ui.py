# -*- coding: utf-8 -*-
"""日房态页新增「批量设置」：按日期区间停用/恢复/改价。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src',
                 'views', 'HouseCalendar.vue')
s = io.open(V, encoding='utf-8').read()

if 'rangeVisible' in s:
    print('已存在')
    raise SystemExit(0)

# 1) 工具栏按钮（放在「预订」按钮之后）
anchor = '<el-button type="success" @click="openBook" data-testid="cal-book">预订</el-button>'
if anchor not in s:
    raise SystemExit('未找到预订按钮')
s = s.replace(anchor, anchor + '''
        <el-button type="warning" plain @click="openRange"
                   data-testid="cal-range">批量设置</el-button>''', 1)

# 2) 弹窗
dialog = '''
    <!-- 批量设置：按区间停用/恢复/改价 -->
    <el-dialog v-model="rangeVisible" title="批量设置日房态" width="560px">
      <el-alert type="info" :closable="false" show-icon
                title="按日期区间批量操作；已预订/已入住的日期不会被改价覆盖" />
      <el-form :model="rf2" label-width="96px" style="margin-top:12px">
        <el-form-item label="房源 ID" required>
          <el-input v-model="rf2.houseId" placeholder="从列表行点「批量设置」自动带入" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="开始日期" required>
            <el-date-picker v-model="rf2.start" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日期" required>
            <el-date-picker v-model="rf2.end" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="操作">
          <el-radio-group v-model="rf2.action">
            <el-radio value="CLOSED">停用（不可售）</el-radio>
            <el-radio value="FREE">恢复可售</el-radio>
            <el-radio value="PRICE">改价</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row v-if="rf2.action === 'PRICE'" :gutter="12">
          <el-col :span="12"><el-form-item label="平日价">
            <el-input v-model="rf2.price" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="周末价">
            <el-input v-model="rf2.weekendPrice" type="number" placeholder="留空则与平日同价" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="rangeVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRange">执行</el-button>
      </template>
    </el-dialog>
'''
i = s.rfind('</template>')
s = s[:i] + dialog + s[i:]

# 3) 逻辑
script = '''
/** 批量设置：区间停用 / 恢复 / 改价 */
const rangeVisible = ref(false)
const rf2 = reactive({ houseId: '', start: '', end: '', action: 'CLOSED',
  price: '', weekendPrice: '' })

function openRange() {
  Object.assign(rf2, { houseId: '', start: '', end: '', action: 'CLOSED',
    price: '', weekendPrice: '' })
  rangeVisible.value = true
}

function rangeForHouse(row) {
  openRange()
  rf2.houseId = String(row.houseId || '')
  const d = row.date || ''
  rf2.start = d
  rf2.end = d
}

async function doRange() {
  if (!rf2.houseId || !rf2.start || !rf2.end) {
    ElMessage.warning('请填写房源与日期区间'); return
  }
  if (rf2.end < rf2.start) {
    ElMessage.warning('结束日期不能早于开始日期'); return
  }
  saving.value = true
  try {
    if (rf2.action === 'PRICE') {
      if (rf2.price === '' || Number(rf2.price) < 0) {
        ElMessage.warning('请填写有效价格'); saving.value = false; return
      }
      const n = await req.post(`/house-calendar/${rf2.houseId}/price-range`, {
        start: rf2.start, end: rf2.end, price: Number(rf2.price),
        weekendPrice: rf2.weekendPrice === '' ? null : Number(rf2.weekendPrice)
      })
      ElMessage.success(`已更新 ${n} 天价格`)
    } else {
      const n = await req.post(`/house-calendar/${rf2.houseId}/status`, {
        start: rf2.start, end: rf2.end, dayStatus: rf2.action,
        remark: rf2.action === 'CLOSED' ? '批量停用' : '批量恢复'
      })
      ElMessage.success(`已更新 ${n} 天房态`)
    }
    rangeVisible.value = false
    reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally { saving.value = false }
}
'''
a = s.find('onMounted(')
s = s[:a] + script + '\n' + s[a:]

# 格子菜单里加「批量设置」入口
s = s.replace("""      <el-dropdown-item v-if="row.dayStatus !== 'FREE'"
                        @click="onDayCommand('open', row)">恢复可售</el-dropdown-item>""",
              """      <el-dropdown-item v-if="row.dayStatus !== 'FREE'"
                        @click="onDayCommand('open', row)">恢复可售</el-dropdown-item>
      <el-dropdown-item @click="rangeForHouse(row)">批量设置…</el-dropdown-item>""", 1)

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('HouseCalendar.vue：批量设置已加')
