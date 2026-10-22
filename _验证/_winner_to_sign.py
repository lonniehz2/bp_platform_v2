# -*- coding: utf-8 -*-
"""从公示中签名单一键进入快捷签约。

1) 后端：PublicityWinnerVO 增加 houseId（前端预填房源）
2) 公示页：名单行加「去签约」→ 跳转 /contracts?personId=..&houseId=..
3) 合同页：读取 query 预填快捷签约弹窗并自动打开
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
B = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')
V = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------- 1) VO 加 houseId ----------
W = os.path.join(B, 'dto', 'PublicityWinnerVO.java')
s = io.open(W, encoding='utf-8').read()
if 'Long houseId' not in s:
    s = s.replace('        Long personId,', '        Long personId,\n        Long houseId,', 1)
    io.open(W, 'w', encoding='utf-8', newline='').write(s)
    print('PublicityWinnerVO：已加 houseId')

# ---------- 2) 服务实现补参 ----------
I = os.path.join(B, 'service', 'impl', 'PublicityServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'r.getHouseId(),' not in s:
    s = s.replace('''            out.add(new com.yundao.bp.biz.dto.PublicityWinnerVO(
                    r.getPersonId(),''',
                  '''            out.add(new com.yundao.bp.biz.dto.PublicityWinnerVO(
                    r.getPersonId(),
                    r.getHouseId(),''', 1)
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('PublicityServiceImpl：已补 houseId')

# ---------- 3) 公示页名单加「去签约」----------
P = os.path.join(V, 'Publicities.vue')
s = io.open(P, encoding='utf-8').read()
if 'goSignFromWinner' not in s:
    # 名单表格末尾加操作列
    s = s.replace('''            <el-table-column prop="resultTypeLabel" label="结果" width="90">''',
                  '''            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row: w }">
                <el-button link type="primary" @click="goSignFromWinner(w)"
                           data-testid="winner-sign">去签约</el-button>
              </template>
            </el-table-column>
            <el-table-column prop="resultTypeLabel" label="结果" width="90">''', 1)

    script = '''
/** 从名单一键签约：带人中转合同页的快捷签约 */
function goSignFromWinner(w) {
  if (!w.personId) { ElMessage.warning('该记录缺少中签人信息'); return }
  router.push({ path: '/contracts',
    query: { personId: String(w.personId), houseId: w.houseId ? String(w.houseId) : '' } })
}
'''
    i = s.find('onMounted(')
    s = s[:i] + script + '\n' + s[i:]
    # 引入 router 与 ElMessage
    if "from 'vue-router'" not in s:
        s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                      "import { ref, reactive, onMounted } from 'vue'\n"
                      "import { useRouter } from 'vue-router'\n"
                      "import { ElMessage } from 'element-plus'", 1)
        s = s.replace('onMounted(', 'const router = useRouter()\n\nonMounted(', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('Publicities.vue：已加「去签约」')

# ---------- 4) 合同页接收参数 ----------
C = os.path.join(V, 'Contracts.vue')
s = io.open(C, encoding='utf-8').read()
if 'prefillQuickSign' not in s:
    script = '''
/** 从公示中签名单跳转进来：预填并打开快捷签约 */
function prefillQuickSign(query) {
  if (!query || !query.personId) return
  openQuickSign()
  qf.personId = String(query.personId)
  if (query.houseId) {
    qf.houseId = String(query.houseId)
    req.get(`/houses/${query.houseId}`).then((h) => {
      if (h) vacantHouses.value = [{ ...h }]
    }).catch(() => {})
  }
}
'''
    anchor = 'onMounted(load)'
    s = s.replace(anchor, script + '\n' + anchor, 1)
    # 在 onMounted 里调用
    s = s.replace('onMounted(load)', '''onMounted(() => {
  load()
  prefillQuickSign(route.query)
})''', 1)
    if 'useRoute' not in s:
        s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                      "import { ref, reactive, onMounted } from 'vue'\nimport { useRoute } from 'vue-router'", 1)
        s = s.replace('const qf = reactive(', 'const route = useRoute()\nconst qf = reactive(', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('Contracts.vue：已支持预填')

print('完成')
