# -*- coding: utf-8 -*-
"""P1 接线（第二批）：轮候退出、走访转工单、年审调租、公示 req 导入。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')


def patch(fn, pairs, note):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old and old in s:
            s = s.replace(old, new, 1)
            n += 1
    if n:
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：应用 %d/%d' % (note, n, len(pairs)))
    return s


# ---------- 公示：补 req 导入 ----------
patch('Publicities.vue', [(
    "import { publicityApi } from '@/api/modules'",
    "import { publicityApi } from '@/api/modules'\nimport req from '@/api/request'")], '公示 req')

# ---------- 轮候：候补退出 ----------
patch('Waitlist.vue', [
    ("""      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>""",
     """      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="doExit(row)">候补退出</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>"""),
    ('</script>', """/** 候补退出：放弃轮候资格，需填原因 */
async function doExit(row) {
  const { value } = await ElMessageBox.prompt('退出原因（如已购商品房/迁出本市）', '候补退出',
    { inputValidator: (v) => (v && v.trim() ? true : '请填写退出原因') })
  await ElMessageBox.confirm('确认该候补家庭退出轮候？退出后需重新申请。', '确认',
    { type: 'warning' })
  await req.post(`/allocation/waiting/${row.id}/exit`, { reason: value })
  ElMessage.success('已退出轮候'); load()
}
</script>""")], '轮候退出')

# ---------- 走访：转工单 ----------
patch('Visits.vue', [
    ("""          <el-button link type="primary" @click="report(row)">登记报告</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>""",
     """          <el-button link type="primary" @click="report(row)">登记报告</el-button>
          <el-button link type="warning" @click="toWorkOrder(row)">转工单</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>"""),
    ('</script>', """/** 走访发现问题 → 转工单处理（如违规使用整改、维修） */
async function toWorkOrder(row) {
  await ElMessageBox.confirm('确认把该走访转为工单？', '转工单', { type: 'warning' })
  await req.post(`/visits/${row.id}/to-workorder`,
    { operatorId: 1, operatorName: '管理员' })
  ElMessage.success('已转工单')
  load()
}
</script>""")], '走访转工单')

# ---------- 年审：复核后调租 ----------
patch('AnnualReviews.vue', [
    ("""          <el-button link type="primary" @click="openReview(row)">复核</el-button>""",
     """          <el-button link type="primary" @click="openReview(row)">复核</el-button>
          <el-button link type="warning" @click="openRent(row)">调租</el-button>"""),
    ('</script>', """/** 复核后调整租金：生成合同变更单 */
const rentVisible = ref(false)
const rentRow = ref({})
const rentForm = reactive({ newMonthlyRent: null, reason: '年审收入变化调租' })

function openRent(row) {
  rentRow.value = row
  rentForm.newMonthlyRent = row.currentRent || row.monthlyRent || null
  rentVisible.value = true
}

async function doRentChange() {
  if (!rentForm.newMonthlyRent) {
    ElMessage.warning('请填写新租金'); return
  }
  await req.post(`/annual-reviews/${rentRow.value.id}/rent-change`, {
    newMonthlyRent: rentForm.newMonthlyRent, reason: rentForm.reason
  })
  ElMessage.success('已生成调租变更单')
  rentVisible.value = false
  load()
}
</script>""")], '年审调租')
