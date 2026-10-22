# -*- coding: utf-8 -*-
"""修正 Bills.vue 公摊分摊：改用 financeApi + 新增 API 方法，去掉不存在的 requestGet/requestPost。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')

# 1) modules.js 增加 generateShared
M = os.path.join(V, 'api', 'modules.js')
s = io.open(M, encoding='utf-8').read()
if 'generateShared' not in s:
    s = s.replace("  generateBatch: (data) => req.post('/fin/bills/generate-batch', data),",
                  "  generateBatch: (data) => req.post('/fin/bills/generate-batch', data),\n"
                  "  generateShared: (data) => req.post('/fin/bills/generate-shared', data),",
                  1)
    io.open(M, 'w', encoding='utf-8', newline='').write(s)
    print('modules.js：generateShared 已加')

# 2) Bills.vue 使用 financeApi
P = os.path.join(V, 'views', 'Bills.vue')
s = io.open(P, encoding='utf-8').read()

s = s.replace('''  if (!orgOptions.value.length) {
    try {
      const d = await financeApi.reqGet ? null : null
    } catch (e) { /* ignore */ }
  }
  try {
    const org = await requestGet('/orgs', { pageNum: 1, pageSize: 100 })
    orgOptions.value = (org && org.rows) || []
  } catch (e) { /* ignore */ }
  try {
    const fi = await requestGet('/fin/fee-items', { pageNum: 1, pageSize: 100 })
    feeItems.value = (fi && fi.rows) || []
  } catch (e) { /* ignore */ }''',
'''  try {
    const org = await financeApi.orgs({ pageNum: 1, pageSize: 100 })
    orgOptions.value = (org && org.rows) || []
  } catch (e) { /* 组织加载失败不阻断 */ }
  try {
    const fi = await financeApi.feeItems({ pageNum: 1, pageSize: 100 })
    feeItems.value = (fi && fi.rows) || []
  } catch (e) { /* 收费项目加载失败不阻断 */ }''', 1)

s = s.replace('''    const r = await requestPost('/fin/bills/generate-shared', {''',
              '''    const r = await financeApi.generateShared({''', 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Bills.vue：改用 financeApi')

# 3) modules.js 补 orgs / feeItems 便捷方法
s = io.open(M, encoding='utf-8').read()
if "feeItems:" not in s or "orgs:" not in s:
    s = s.replace("  bills: (params) => req.get('/fin/bills', { params }),",
                  "  bills: (params) => req.get('/fin/bills', { params }),\n"
                  "  orgs: (params) => req.get('/orgs', { params }),\n"
                  "  feeItems: (params) => req.get('/fin/fee-items', { params }),",
                  1)
    io.open(M, 'w', encoding='utf-8', newline='').write(s)
    print('modules.js：orgs/feeItems 已加')
