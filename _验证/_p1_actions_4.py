# -*- coding: utf-8 -*-
"""P1 接线（第三批）：补贴发放失败、合同变更创建入口统一。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')


def patch(fn, pairs, note):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old in s and new.split('\n')[0] not in s.replace(old, '', 1):
            s = s.replace(old, new, 1)
            n += 1
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：%d/%d' % (note, n, len(pairs)))


# ---------- 补贴：发放失败 ----------
patch('Subsidies.vue', [
    ("""          <el-button link type="success" :disabled="row.recordStatus !== 'PENDING'"
                     @click="confirm(row)">确认发放</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>""",
     """          <el-button link type="success" :disabled="row.recordStatus !== 'PENDING'"
                     @click="confirm(row)">确认发放</el-button>
          <el-button link type="danger" :disabled="row.recordStatus !== 'PENDING'"
                     @click="doFail(row)">发放失败</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>"""),
    ('</script>', """/** 发放失败：银行退回/账户异常等，记录原因便于补发 */
async function doFail(row) {
  const { value } = await ElMessageBox.prompt('失败原因（如账户异常/银行退回）', '标记发放失败',
    { inputValidator: (v) => (v && v.trim() ? true : '请填写失败原因') })
  await req.post(`/fin/subsidies/records/${row.id}/fail`, { reason: value })
  ElMessage.success('已标记失败')
  load()
}
</script>""")], '补贴发放失败')

# 补贴页若缺 ElMessageBox / req，补上
p = os.path.join(V, 'Subsidies.vue')
s = io.open(p, encoding='utf-8').read()
changed = False
if 'ElMessageBox' in s and 'ElMessageBox }' not in s and 'ElMessageBox,' not in s.split('\n')[0:0]:
    if "import { ElMessage } from 'element-plus'" in s:
        s = s.replace("import { ElMessage } from 'element-plus'",
                      "import { ElMessage, ElMessageBox } from 'element-plus'", 1)
        changed = True
if "'@/api/request'" not in s:
    s = s.replace("import { financeApi } from '@/api/modules'",
                  "import { financeApi } from '@/api/modules'\nimport req from '@/api/request'", 1)
    changed = True
if changed:
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('补贴导入已检查')
