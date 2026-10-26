# -*- coding: utf-8 -*-
"""补齐 P1 新增动作所需导入，并给年审补调租弹窗模板。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')


def fix(fn, pairs, note):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old in s and new not in s:
            s = s.replace(old, new, 1)
            n += 1
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s：应用 %d/%d' % (note, n, len(pairs)))


# 轮候：需要 ElMessageBox
fix('Waitlist.vue', [("import { ElMessage } from 'element-plus'",
                     "import { ElMessage, ElMessageBox } from 'element-plus'")], '轮候导入')

# 走访：需要 req
fix('Visits.vue', [("import { visitApi } from '@/api/modules'",
                   "import { visitApi } from '@/api/modules'\nimport req from '@/api/request'")],
    '走访导入')

# 年审：需要 ElMessageBox + req + reactive + 弹窗
fix('AnnualReviews.vue', [
    ("import { ElMessage } from 'element-plus'",
     "import { ElMessage, ElMessageBox } from 'element-plus'"),
    ("import { annualReviewApi } from '@/api/modules'",
     "import { annualReviewApi } from '@/api/modules'\nimport req from '@/api/request'"),
    ("import { ref, reactive, onMounted } from 'vue'",
     "import { ref, reactive, onMounted } from 'vue'"),
], '年审导入')

# 年审：若原来是 ref,onMounted 需补 reactive
p = os.path.join(V, 'AnnualReviews.vue')
s = io.open(p, encoding='utf-8').read()
if 'reactive(' in s and "import { ref, reactive, onMounted }" not in s:
    s = s.replace("import { ref, onMounted } from 'vue'",
                  "import { ref, reactive, onMounted } from 'vue'", 1)

# 年审：补调租弹窗（放在最后一个 </el-drawer> 后、根 div 结束前）
if 'rentVisible' in s and 'v-model="rentVisible"' not in s:
    anchor = "    <el-drawer"
    idx = s.rfind('</el-drawer>')
    if idx > 0:
        dlg = """
    <el-dialog v-model="rentVisible" title="复核后调租" width="460px">
      <el-form :model="rentForm" label-width="110px">
        <el-form-item label="新租金（元）" required>
          <el-input v-model.number="rentForm.newMonthlyRent" />
        </el-form-item>
        <el-form-item label="调租原因">
          <el-input v-model="rentForm.reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rentVisible = false">取消</el-button>
        <el-button type="primary" @click="doRentChange">生成变更单</el-button>
      </template>
    </el-dialog>
"""
        s = s[:idx + len('</el-drawer>')] + dlg + s[idx + len('</el-drawer>'):]
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('年审弹窗已补')
