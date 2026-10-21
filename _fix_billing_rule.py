# -*- coding: utf-8 -*-
"""按真实字段修正计费规则表单与验证"""
import io
import json
import urllib.error
import urllib.request

# ---------- 1) 前端表单字段修正 ----------
P = r'D:\Work\业务平台开发\frontend\src\views\FeeItems.vue'
s = io.open(P, encoding='utf-8').read()

old_form = '''        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="计费项目ID" required>
            <el-input v-model.number="r.feeItemId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则名称">
            <el-input v-model="r.ruleName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="生效日期">
            <el-date-picker v-model="r.effectiveDate" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="失效日期">
            <el-date-picker v-model="r.expireDate" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则单价">
            <el-input-number v-model="r.unitPrice" :precision="2" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织ID">
            <el-input v-model.number="r.orgId" /></el-form-item></el-col>
        </el-row>'''

new_form = '''        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="规则编码" required>
            <el-input v-model="r.ruleCode" placeholder="如 RENT-STD-2026" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则名称" required>
            <el-input v-model="r.ruleName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计费项目ID" required>
            <el-input v-model.number="r.feeItemId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则类型" required>
            <el-select v-model="r.ruleType" style="width:100%">
              <el-option label="标准价 STANDARD" value="STANDARD" />
              <el-option label="阶梯价 TIERED" value="TIERED" />
              <el-option label="折扣 DISCOUNT" value="DISCOUNT" />
              <el-option label="减免 EXEMPT" value="EXEMPT" />
            </el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="价格配置" required>
            <el-input v-model="r.priceConfig" type="textarea" :rows="3"
                      placeholder='JSON，如 {"price":150.00} 或阶梯 {"tiers":[{"max":50,"price":1.2}]}' />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="生效日期">
            <el-date-picker v-model="r.effectiveStart" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="失效日期">
            <el-date-picker v-model="r.effectiveEnd" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织ID">
            <el-input v-model.number="r.orgId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="优先级">
            <el-input-number v-model="r.priority" :min="1" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用保障类型">
            <el-select v-model="r.securityType" clearable style="width:100%">
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="保租房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用收入档位">
            <el-select v-model="r.incomeLevel" clearable style="width:100%">
              <el-option label="低保 LOW" value="LOW" />
              <el-option label="低收入 LOW_INCOME" value="LOW_INCOME" />
              <el-option label="中低收入 MIDDLE_LOW" value="MIDDLE_LOW" />
              <el-option label="普通 NORMAL" value="NORMAL" />
            </el-select></el-form-item></el-col>
        </el-row>'''

if old_form in s:
    s = s.replace(old_form, new_form, 1)

# 状态对象
s = s.replace("const r = reactive({ feeItemId: null, ruleName: '', effectiveDate: '',\n"
              "  expireDate: '', unitPrice: null, orgId: null })",
              "const r = reactive({ ruleCode: '', ruleName: '', feeItemId: null,\n"
              "  ruleType: 'STANDARD', priceConfig: '{\"price\": 150.00}',\n"
              "  effectiveStart: '', effectiveEnd: '', orgId: null, priority: 1,\n"
              "  securityType: '', incomeLevel: '' })", 1)

# 提交校验
s = s.replace("""async function doCreateRule() {
  if (!r.feeItemId) { ElMessage.warning('请填写计费项目ID'); return }""",
              """async function doCreateRule() {
  if (!r.ruleCode || !r.ruleName || !r.feeItemId || !r.priceConfig) {
    ElMessage.warning('规则编码、名称、计费项目、价格配置为必填'); return
  }
  try { JSON.parse(r.priceConfig) } catch (e) {
    ElMessage.error('价格配置必须是合法 JSON'); return
  }""", 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ FeeItems.vue 计费规则表单按真实 DTO 修正')

# ---------- 2) 真实接口验证 ----------
BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

st, r = call('GET', '/api/v1/fin/fee-items?pageNum=1&pageSize=5', None, TOK)
fid = ((r.get('data') or {}).get('rows') or [{}])[0].get('id')
print('\n用真实项目 %s 建规则' % fid)
st, r = call('POST', '/api/v1/fin/billing-rules', {
    'ruleCode': 'RULE-TEST-1', 'ruleName': '测试标准价规则', 'feeItemId': fid,
    'orgId': ORG, 'ruleType': 'STANDARD', 'priceConfig': '{"price":150.00}',
    'effectiveStart': '2026-01-01', 'priority': 1}, TOK)
rid = (r.get('data') or {}).get('id')
print('  建规则：%s %s → %s %s' % (st, r.get('code'), rid, str(r.get('message'))[:50]))
if rid:
    st, r = call('POST', '/api/v1/fin/billing-rules/%s/approve' % rid, None, TOK)
    print('  审批：%s %s' % (st, r.get('code')))
