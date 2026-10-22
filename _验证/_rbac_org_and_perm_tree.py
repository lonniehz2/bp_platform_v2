# -*- coding: utf-8 -*-
"""角色/权限页三项改进：

1. 新增用户：组织必填 + 下拉选择（组织决定数据归属，必须明确）
2. 权限配置：按「模块 → 资源 → 操作」三级展示，子权限向右缩进
3. 数据范围四项保持不变（ALL/ORG/ORG_SUB/SELF）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Rbac.vue')

# 1) 组织下拉
ORG_OLD = '''        <el-form-item label="组织ID">
          <el-input v-model="uf.orgId" /></el-form-item>'''
ORG_NEW = '''        <el-form-item label="所属组织" required>
          <el-select v-model="uf.orgId" filterable clearable style="width:100%"
                     placeholder="选择组织（决定数据归属）" data-testid="user-org">
            <el-option v-for="o in orgOptions" :key="o.id"
                       :label="o.orgName" :value="String(o.id)" />
          </el-select></el-form-item>'''

# 2) 权限分组：按模块→资源两级缩进
GROUP_TPL_OLD = '''          <div class="perm-group-body">
            <el-checkbox
              v-for="p in g.items" :key="p.id"
              :model-value="checkedPerms.includes(String(p.id))"
              :label="`${p.permName}`"
              :title="p.permCode"
              @change="(v) => togglePerm(p, v)" />
          </div>'''
GROUP_TPL_NEW = '''          <div class="perm-group-body">
            <div v-for="res in g.resources" :key="res.key" class="perm-res">
              <div class="perm-res-head">
                <el-checkbox
                  :model-value="res.items.every((p) => checkedPerms.includes(String(p.id)))"
                  :indeterminate="!res.items.every((p) => checkedPerms.includes(String(p.id)))
                    && res.items.some((p) => checkedPerms.includes(String(p.id)))"
                  @change="(v) => toggleGroup(res, v)">
                  {{ res.label }}
                </el-checkbox>
              </div>
              <div class="perm-actions">
                <el-checkbox
                  v-for="p in res.items" :key="p.id"
                  :model-value="checkedPerms.includes(String(p.id))"
                  :label="p.permName"
                  :title="p.permCode"
                  @change="(v) => togglePerm(p, v)" />
              </div>
            </div>
          </div>'''

CSS_OLD = '''.perm-group { border: 1px solid #ebeef5; border-radius: 4px; margin-bottom: 8px; }
.perm-group-head { background: #fafafa; padding: 6px 10px; border-bottom: 1px solid #ebeef5; }
.perm-group-body { padding: 8px 12px; display: flex; flex-wrap: wrap; gap: 6px 16px; }'''
CSS_NEW = '''.perm-group { border: 1px solid #ebeef5; border-radius: 4px; margin-bottom: 8px; }
.perm-group-head { background: #fafafa; padding: 6px 10px; border-bottom: 1px solid #ebeef5; }
.perm-group-body { padding: 6px 12px 10px; }
/* 二级：资源；三级：操作，逐级缩进，便于看清层级 */
.perm-res { margin-top: 6px; }
.perm-res-head { padding-left: 18px; }
.perm-actions { padding-left: 44px; display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 2px; }'''

# 3) permGroups 计算：增加 resources 层
CALC_OLD = '''  return Array.from(map.entries())
    .map(([key, items]) => ({ key, label: MODULE_LABEL[key] || key, items }))
    .sort((a, b) => a.key.localeCompare(b.key))'''
CALC_NEW = '''  const RES_LABEL = {
    user: '用户', role: '角色', perm: '权限', contract: '合同', person: '人员',
    house: '房源', bill: '账单', feeItem: '计费项', deposit: '押金', arrear: '催缴',
    report: '报表', screen: '大屏', audit: '审计', dict: '字典', config: '参数',
    app: '应用', log: '日志', keyring: '钥匙', grant: '授权', visit: '走访',
    complaint: '投诉', appeal: '申诉', credit: '信用', alert: '告警', workorder: '工单'
  }
  const ACTION_LABEL = {
    list: '查看', query: '查询', detail: '详情', create: '新增', update: '修改',
    delete: '删除', assign: '授权', audit: '审核', approve: '审批', export: '导出',
    publish: '发布', disable: '停用', manage: '管理', revoke: '撤销', print: '打印'
  }
  return Array.from(map.entries())
    .map(([key, items]) => {
      // 模块内再按资源分组：permCode 形如 iam:user:list
      const byRes = new Map()
      for (const p of items) {
        const parts = String(p.permCode || '').split(':')
        const res = parts[1] || 'other'
        if (!byRes.has(res)) byRes.set(res, [])
        byRes.get(res).push({ ...p, actionLabel: ACTION_LABEL[parts[2]] || parts[2] || '' })
      }
      const resources = Array.from(byRes.entries())
        .map(([rk, list]) => ({ key: rk, label: RES_LABEL[rk] || rk, items: list }))
        .sort((a, b) => a.key.localeCompare(b.key))
      return { key, label: MODULE_LABEL[key] || key, items, resources }
    })
    .sort((a, b) => a.key.localeCompare(b.key))'''

# 4) 组织选项加载
SCRIPT_ADD = '''
/** 组织下拉选项（新增用户时必填，决定数据归属） */
const orgOptions = ref([])
async function loadOrgOptions() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = d.rows || d || []
  } catch (e) { orgOptions.value = [] }
}
'''


def main():
    s = io.open(P, encoding='utf-8').read()
    n = 0

    if ORG_OLD in s:
        s = s.replace(ORG_OLD, ORG_NEW, 1)
        n += 1
    if GROUP_TPL_OLD in s:
        s = s.replace(GROUP_TPL_OLD, GROUP_TPL_NEW, 1)
        n += 1
    if CSS_OLD in s:
        s = s.replace(CSS_OLD, CSS_NEW, 1)
        n += 1
    if CALC_OLD in s:
        s = s.replace(CALC_OLD, CALC_NEW, 1)
        n += 1

    # 组织选项状态 + 加载
    if 'const orgOptions' not in s:
        s = s.replace("const roleCfgVisible = ref(false)", SCRIPT_ADD + "\nconst roleCfgVisible = ref(false)", 1)
        s = s.replace("onMounted(load)", "onMounted(() => { loadOrgOptions(); load() })", 1)
        n += 1

    # 新增用户校验：组织必填
    if "ElMessage.warning('请填写账号/密码/姓名')" in s:
        s = s.replace("ElMessage.warning('请填写账号/密码/姓名')",
                      "ElMessage.warning('请填写账号/密码/姓名/组织')", 1)
    if "if (!uf.username || !uf.password || !uf.realName)" in s:
        s = s.replace("if (!uf.username || !uf.password || !uf.realName)",
                      "if (!uf.username || !uf.password || !uf.realName || !uf.orgId)", 1)
        n += 1

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('Rbac.vue 改动 %d 处' % n)


if __name__ == '__main__':
    main()
