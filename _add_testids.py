# -*- coding: utf-8 -*-
"""给关键表单加 data-testid，并把 E2E 改为语义定位"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

# ---------- 1) 人员表单 ----------
P = os.path.join(V, 'Persons.vue')
s = io.open(P, encoding='utf-8').read()
PAIRS = [
    ('<el-input v-model="pf.personName" />',
     '<el-input v-model="pf.personName" data-testid="person-name" />'),
    ('<el-input v-model="pf.phone" />',
     '<el-input v-model="pf.phone" data-testid="person-phone" />'),
]
n = 0
for a, b in PAIRS:
    if a in s and 'data-testid' not in a:
        s = s.replace(a, b, 1); n += 1
io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ Persons.vue 加 %d 个 testid' % n)

# ---------- 2) 计费项目表单 ----------
P2 = os.path.join(V, 'FeeItems.vue')
t = io.open(P2, encoding='utf-8').read()
PAIRS2 = [
    ('<el-input v-model="f.itemCode" />',
     '<el-input v-model="f.itemCode" data-testid="fee-code" />'),
    ('<el-input v-model="f.itemName" />',
     '<el-input v-model="f.itemName" data-testid="fee-name" />'),
    ('<el-input-number v-model="f.unitPrice" :min="0" :precision="2"\n                             style="width:100%" />',
     '<el-input-number v-model="f.unitPrice" :min="0" :precision="2"\n'
     '                             data-testid="fee-price" style="width:100%" />'),
]
n2 = 0
for a, b in PAIRS2:
    if a in t:
        t = t.replace(a, b, 1); n2 += 1
io.open(P2, 'w', encoding='utf-8').write(t)
print('  ✓ FeeItems.vue 加 %d 个 testid' % n2)

# ---------- 3) 合同表单 ----------
P3 = os.path.join(V, 'Contracts.vue')
u = io.open(P3, encoding='utf-8').read()
PAIRS3 = [
    ('v-model.number="c.lesseePersonId"', 'v-model.number="c.lesseePersonId" data-testid="c-lessee-id"'),
    ('v-model="c.lesseeName"', 'v-model="c.lesseeName" data-testid="c-lessee-name"'),
    ('v-model="c.lesseePhone"', 'v-model="c.lesseePhone" data-testid="c-lessee-phone"'),
    ('v-model.number="c.houseId"', 'v-model.number="c.houseId" data-testid="c-house-id"'),
    ('v-model="c.houseAddress"', 'v-model="c.houseAddress" data-testid="c-address"'),
    ('v-model.number="c.monthlyRent"', 'v-model.number="c.monthlyRent" data-testid="c-rent"'),
    ('v-model.number="c.depositAmount"', 'v-model.number="c.depositAmount" data-testid="c-deposit"'),
]
n3 = 0
for a, b in PAIRS3:
    if a in u and 'data-testid' not in u[max(0, u.find(a) - 40):u.find(a)]:
        u = u.replace(a, b, 1); n3 += 1
io.open(P3, 'w', encoding='utf-8').write(u)
print('  ✓ Contracts.vue 加 %d 个 testid' % n3)

# ---------- 4) E2E 改用 testid ----------
E = r'D:\Work\业务平台开发\_验证\ui_e2e.js'
e = io.open(E, encoding='utf-8').read()

HELPER = '''  /** 按 data-testid 填值（语义定位，不依赖顺序） */
  const fillTid = async (tid, val) => page.evaluate((id, v) => {
    const el = document.querySelector('[data-testid="' + id + '"]')
    if (!el) return false
    const input = el.tagName === 'INPUT' ? el : el.querySelector('input')
    if (!input) return false
    input.focus(); input.value = v
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
    input.blur()
    return true
  }, tid, val)
'''
if 'fillTid' not in e:
    e = e.replace('  const fillDlg = async', HELPER + '\n  const fillDlg = async', 1)

# 人员流程
e = e.replace("    const okName = await fillDlg(0, name)          // 0=姓名\n"
              "    await fillDlg(2, '139' + stamp.padStart(8, '0').slice(0, 8))   // 2=手机号",
              "    const okName = await fillTid('person-name', name)\n"
              "    await fillTid('person-phone', '139' + stamp.padStart(8, '0').slice(0, 8))")
# 计费流程
e = e.replace("    await fillDlg(0, 'E2E' + stamp)\n"
              "    await fillDlg(1, 'E2E测试项目' + stamp)\n"
              "    await page.evaluate(() => {\n"
              "      const d = document.querySelector('.el-dialog')\n"
              "      const n = d && d.querySelector('input[type=number], .el-input-number input')\n"
              "      if (n) { n.focus(); n.value = '12.5'; n.dispatchEvent(new Event('input', { bubbles: true })); n.blur() }\n"
              "    })",
              "    await fillTid('fee-code', 'E2E' + stamp)\n"
              "    await fillTid('fee-name', 'E2E测试项目' + stamp)\n"
              "    await fillTid('fee-price', '12.5')")
# 合同流程
e = e.replace("""      await fill('承租人ID', String(p.id))
      await fill('承租人姓名', p.personName || 'E2E承租人')
      await fill('联系电话', '13900001111')
      await fill('房源ID', String(h.id))
      await fill('房屋地址', h.houseName || 'E2E地址')
      await fill('月租金', '1000')
      await fill('押金', '1000')""",
              """      await fillTid('c-lessee-id', String(p.id))
      await fillTid('c-lessee-name', p.personName || 'E2E承租人')
      await fillTid('c-lessee-phone', '13900001111')
      await fillTid('c-house-id', String(h.id))
      await fillTid('c-address', h.houseName || 'E2E地址')
      await fillTid('c-rent', '1000')
      await fillTid('c-deposit', '1000')""")

io.open(E, 'w', encoding='utf-8').write(e)
print('  ✓ ui_e2e.js 改用 data-testid 定位')
