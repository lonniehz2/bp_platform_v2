# -*- coding: utf-8 -*-
"""角色配置权限区：区分「页面（菜单）」与「功能（按钮）」，并补全中文映射。

- 页面权限：permCode 以 page: 开头 → 单独分区，按菜单名称列示
- 功能权限：其余 → 按 模块 → 资源 → 操作 三级缩进
- 资源/操作的中文名补全（credit/manage/adapter/test 等此前显示英文）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Rbac.vue')

# 1) 模板：权限区改为两段
TPL_OLD = '''      <el-scrollbar max-height="380px">
        <div v-for="g in permGroups" :key="g.key" class="perm-group">'''
TPL_NEW = '''      <el-tabs v-model="permTab" style="margin-top:4px">
        <el-tab-pane label="页面权限（菜单）" name="page">
          <div class="muted" style="margin-bottom:6px">
            控制该角色能看到哪些菜单与页面；勾选后对应菜单才会出现
          </div>
          <el-scrollbar max-height="330px">
            <div class="perm-group">
              <div class="perm-group-body">
                <el-checkbox
                  v-for="p in pagePerms" :key="p.id"
                  :model-value="checkedPerms.includes(String(p.id))"
                  :label="p.permName"
                  :title="p.routePath || p.permCode"
                  @change="(v) => togglePerm(p, v)" />
              </div>
            </div>
          </el-scrollbar>
        </el-tab-pane>
        <el-tab-pane label="功能权限（操作）" name="func">
          <div class="muted" style="margin-bottom:6px">
            控制该角色能执行哪些操作（新增/修改/审核/导出等按钮级权限）
          </div>
          <el-scrollbar max-height="330px">
        <div v-for="g in permGroups" :key="g.key" class="perm-group">'''

TPL_TAIL_OLD = '''            </div>
          </div>
        </div>
      </el-scrollbar>
'''
TPL_TAIL_NEW = '''            </div>
          </div>
        </div>
          </el-scrollbar>
        </el-tab-pane>
      </el-tabs>
'''

# 2) 计算属性：拆分 pagePerms / permGroups（排除 page:）
CALC_OLD = '''const permGroups = computed(() => {
  const map = new Map()
  for (const p of perms.value) {'''
CALC_NEW = '''/** 页面级权限（page:xxx:view）——对应菜单可见性 */
const pagePerms = computed(() =>
  perms.value.filter((p) => String(p.permCode || '').startsWith('page:'))
    .sort((a, b) => String(a.permName).localeCompare(String(b.permName), 'zh')))

/** 功能权限（按钮/接口级），按模块→资源→操作分组 */
const permGroups = computed(() => {
  const map = new Map()
  for (const p of perms.value) {
    if (String(p.permCode || '').startsWith('page:')) continue'''

# 3) 资源/操作中文补全
RES_OLD = '''  const RES_LABEL = {
    user: '用户', role: '角色', perm: '权限', contract: '合同', person: '人员',
    house: '房源', bill: '账单', feeItem: '计费项', deposit: '押金', arrear: '催缴',
    report: '报表', screen: '大屏', audit: '审计', dict: '字典', config: '参数',
    app: '应用', log: '日志', keyring: '钥匙', grant: '授权', visit: '走访',
    complaint: '投诉', appeal: '申诉', credit: '信用', alert: '告警', workorder: '工单'
  }'''
RES_NEW = '''  const RES_LABEL = {
    user: '用户', role: '角色', perm: '权限', contract: '合同', person: '人员',
    house: '房源', bill: '账单', feeItem: '计费项', deposit: '押金', arrear: '催缴',
    report: '报表', screen: '大屏', audit: '审计', dict: '字典', config: '参数',
    app: '应用', log: '日志', keyring: '钥匙', grant: '授权', visit: '走访',
    complaint: '投诉', appeal: '申诉', credit: '信用', alert: '告警', workorder: '工单',
    adapter: '适配器', test: '测试', manage: '管理', space: '空间', device: '设备',
    access: '通行', payment: '收款', refund: '退款', subsidy: '补贴', dunning: '催缴',
    reconcile: '对账', cashflow: '资金流水', exchange: '换房', termination: '退租',
    allocation: '配租', application: '申请', review: '年审', publicity: '公示',
    open: '开放平台', webhook: 'Webhook', screen2: '大屏'
  }'''
ACT_OLD = '''  const ACTION_LABEL = {
    list: '查看', query: '查询', detail: '详情', create: '新增', update: '修改',
    delete: '删除', assign: '授权', audit: '审核', approve: '审批', export: '导出',
    publish: '发布', disable: '停用', manage: '管理', revoke: '撤销', print: '打印'
  }'''
ACT_NEW = '''  const ACTION_LABEL = {
    list: '查看', query: '查询', detail: '详情', create: '新增', update: '修改',
    delete: '删除', assign: '授权', audit: '审核', approve: '审批', export: '导出',
    publish: '发布', disable: '停用', manage: '管理', revoke: '撤销', print: '打印',
    view: '查看', edit: '编辑', handle: '处理', submit: '提交', cancel: '作废',
    sign: '签约', grant: '授权', scan: '扫描', recalc: '重算', freeze: '冻结',
    unfreeze: '解冻', run: '执行', sync: '同步', send: '发送', broadcast: '广播'
  }'''


def main():
    s = io.open(P, encoding='utf-8').read()
    n = 0
    for old, new in ((TPL_OLD, TPL_NEW), (TPL_TAIL_OLD, TPL_TAIL_NEW),
                     (CALC_OLD, CALC_NEW), (RES_OLD, RES_NEW), (ACT_OLD, ACT_NEW)):
        if old in s:
            s = s.replace(old, new, 1)
            n += 1
    # permTab 状态
    if 'const permTab' not in s:
        s = s.replace("const roleCfgVisible = ref(false)",
                      "const roleCfgVisible = ref(false)\nconst permTab = ref('page')", 1)
        n += 1
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('Rbac.vue 改动 %d 处' % n)


if __name__ == '__main__':
    main()
