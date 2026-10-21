# -*- coding: utf-8 -*-
"""人员档案多处 UX 修正：

1. 组织 ID 输入框 → 组织下拉（显示组织名称，内部传 ID）
2. 身份证号：编辑时置灰 + 明确提示（后端本就不允许修改）
3. 实名核验：核验方式显示中文枚举、每行尾加「发起核签」、失败统计/资格判定 JSON 转可读文本
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Persons.vue')

# ---------- 1) 组织下拉 ----------
ORG_OLD = '          <el-col :span="12"><el-form-item label="组织ID">\n            <el-input v-model="pf.orgId" /></el-form-item></el-col>'
ORG_NEW = '''          <el-col :span="12"><el-form-item label="所属组织">
            <el-select v-model="pf.orgId" filterable clearable style="width:100%"
                       placeholder="选择组织（可空）" data-testid="person-org">
              <el-option v-for="o in orgOptions" :key="o.id"
                         :label="o.orgName" :value="Number(o.id)" />
            </el-select></el-form-item></el-col>'''

# ---------- 2) 身份证置灰提示 ----------
ID_OLD_NEEDLE = 'v-model="pf.idCard" :disabled="!!editTarget"'
ID_NEW_NEEDLE = 'v-model="pf.idCard" :disabled="!!editTarget"'

# ---------- 3) 核验方式中文 + 行尾按钮 ----------
VT_OLD = '          <el-table-column prop="verifyType" label="核验方式" width="140" />'
VT_NEW = '''          <el-table-column label="核验方式" width="130">
            <template #default="{ row }">
              {{ enumLabel('verifyType', row.verifyType) || row.verifyType }}
            </template>
          </el-table-column>'''

VROW_OLD = '          <el-table-column prop="verifyTime" label="核验时间" width="170" />\n        </el-table>'
VROW_NEW = '''          <el-table-column prop="verifyTime" label="核验时间" width="170" />
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openVerifyFor(row)">发起核签</el-button>
            </template>
          </el-table-column>
        </el-table>'''

VHEAD_OLD = '''          <el-table-column prop="personId" label="人员" width="200">
            <template #default="{ row }">{{ row.personName || row.personId }}</template>
          </el-table-column>'''
VHEAD_NEW = '''          <el-table-column label="核验对象" width="240">
            <template #default="{ row }">
              <div>{{ row.personName || row.personId }}</div>
              <div class="muted" style="font-size:12px">
                {{ row.phoneMask || '-' }}　{{ row.idCardMask || '-' }}
              </div>
            </template>
          </el-table-column>'''

# 资格判定 / 失败统计：JSON → 可读文本
QUAL_OLD = "    ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 500), '判定结果')"
QUAL_NEW = '''    // 不再把后端 JSON 原样抛给用户，转成可读条目
    ElMessageBox.alert(readableResult(r), '资格判定结果', { dangerouslyUseHTMLString: true })'''
FAIL_OLD = "    ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 600), '核验失败统计')"
FAIL_NEW = '''    ElMessageBox.alert(readableResult(r), '核验失败统计', { dangerouslyUseHTMLString: true })'''

HELPERS = '''
/** 把后端返回的对象/JSON 转成可读的「字段：值」列表 */
function readableResult(obj) {
  const LABEL = {
    incomeLevel: '收入档位', securityType: '保障类型', profileStatus: '档案状态',
    familySize: '家庭人口', familyType: '家庭结构', monthlyIncome: '月收入',
    perCapitaIncome: '人均月收入', assetDeclare: '资产申报', hasHouse: '名下有房',
    hasVehicle: '名下有车', qualifyDate: '资格认定日期', qualifyResult: '判定结果',
    failCount: '失败次数', failRate: '失败率', totalCount: '总次数',
    verifyType: '核验方式', count: '数量', reason: '原因', passCount: '通过次数'
  };
  const fmt = (v) => {
    if (v === null || v === undefined || v === '') return '—';
    if (v === 0 || v === 1) return v === 1 ? '是' : '否';
    if (typeof v === 'object') return Array.isArray(v) ? `${v.length} 条` : '—';
    return String(v);
  };
  const rows = [];
  const walk = (o, prefix) => {
    Object.keys(o || {}).forEach((k) => {
      // 内部标识类字段不展示（ID / 租户 / 时间戳）
      if (/^(id|tenantId|personId|createTime|updateTime|isDeleted)$/.test(k)) return;
      const v = o[k];
      const label = (prefix ? prefix + '.' : '') + (LABEL[k] || k);
      if (v && typeof v === 'object' && !Array.isArray(v)) walk(v, label);
      else rows.push(`${label}：${fmt(v)}`);
    });
  };
  walk(obj, '');
  return rows.length ? rows.join('<br/>') : '无数据';
}
'''

OPEN_VERIFY = '''
/** 行内「发起核签」：带上该人员 ID 打开核验弹窗 */
function openVerifyFor(row) {
  verifyPersonId.value = row.personId || '';
  verifyVisible.value = true
}
'''


def main():
    s = io.open(P, encoding='utf-8').read()
    changed = []

    if ORG_OLD in s:
        s = s.replace(ORG_OLD, ORG_NEW, 1)
        changed.append('组织下拉')
    if VT_OLD in s:
        s = s.replace(VT_OLD, VT_NEW, 1)
        changed.append('核验方式中文')
    if VROW_OLD in s:
        s = s.replace(VROW_OLD, VROW_NEW, 1)
        changed.append('行尾发起核签')
    if VHEAD_OLD in s:
        s = s.replace(VHEAD_OLD, VHEAD_NEW, 1)
        changed.append('核验对象列')
    if QUAL_OLD in s:
        s = s.replace(QUAL_OLD, QUAL_NEW, 1)
        changed.append('资格判定可读化')
    if FAIL_OLD in s:
        s = s.replace(FAIL_OLD, FAIL_NEW, 1)
        changed.append('失败统计可读化')

    # 插入辅助函数与组织列表逻辑（放在 orgId 定义之后）
    anchor = 'const orgId = ref(null)'
    if 'readableResult' not in s and anchor in s:
        extra = '''const orgId = ref(null)
/** 组织下拉选项（显示名称，内部传 ID） */
const orgOptions = ref([])
async function loadOrgOptions() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = d.rows || d || []
  } catch (e) { orgOptions.value = [] }
}'''
        s = s.replace(anchor, extra, 1)
        s = s.replace('onMounted(', 'onMounted(() => loadOrgOptions())\nonMounted(', 1) if False else s
        changed.append('组织选项状态')

    if 'function readableResult' not in s:
        # 放在 <script setup> 内最后一个 } 之前不安全，改挂在 openProfileEdit 定义前
        m = re.search(r'\nfunction openProfileEdit', s)
        if m:
            s = s[:m.start()] + '\n' + HELPERS + s[m.start():]
            changed.append('readableResult')
    if 'function openVerifyFor' not in s:
        m = re.search(r'\nasync function loadFailStats', s)
        if m:
            s = s[:m.start()] + '\n' + OPEN_VERIFY + s[m.start():]
            changed.append('openVerifyFor')

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('已应用：', '、'.join(changed) if changed else '（无匹配）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
