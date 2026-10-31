# -*- coding: utf-8 -*-
import io
import os

V = r'..\frontend\src\views'

# 1) 合同：watch 移到 c 声明之后；组织默认不再写死 1
p = os.path.join(V, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
watch_block = '''/** 选承租人：自动带出姓名/电话/脱敏证件 */
watch(() => c.lesseePersonId, async (v) => {
  if (!v) return
  try {
    const p = await req.get('/persons/' + v)
    if (!c.lesseeName) c.lesseeName = p.personName || ''
    if (!c.lesseePhone) c.lesseePhone = p.phone || ''
    if (!c.lesseeIdCardMask) c.lesseeIdCardMask = p.idCardMask || ''
  } catch (e) { /* 忽略 */ }
})

'''
if watch_block in s:
    s = s.replace(watch_block, '', 1)
    anchor = "const c = reactive({ contractType: 'PUBLIC_RENTAL', orgId: 1, lessorOrgId: 1, lesseePersonId: null,"
    if anchor in s:
        s = s.replace(anchor,
                      "const c = reactive({ contractType: 'PUBLIC_RENTAL', orgId: null, lessorOrgId: null, lesseePersonId: null,", 1)
        # 在 c 声明块结束后插入 watch
        end = s.find('const sg = reactive(', s.find(anchor if anchor in s else 'const c = reactive('))
        s = s[:end] + watch_block + s[end:]
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print('contracts watch/org fixed')

# 2) 其它表单：组织默认不再写死 1（避免提交不存在的组织 id=1）
for fn in ['AnnualReviews.vue', 'Applications.vue', 'Bills.vue', 'Subsidies.vue']:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    s2 = s.replace('orgId: 1', 'orgId: null')
    if s2 != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
        print('org default fixed', fn)
