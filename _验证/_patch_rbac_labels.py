# -*- coding: utf-8 -*-
import io

# 1) enums.js: dataScope / userType 覆盖
p = r'..\frontend\src\constants\enums.js'
s = io.open(p, encoding='utf-8').read()
if 'dataScope:' not in s:
    s = s.replace("const TYPE_OVERRIDE = {",
                  "const TYPE_OVERRIDE = {\n"
                  "  dataScope: { ALL: '全部数据', ORG: '本组织', ORG_SUB: '本组织及下级', SELF: '仅本人' },\n"
                  "  userType: { STAFF: '工作人员', TENANT: '承租人', GOV: '政府', PLATFORM: '平台' },", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('enums updated')

# 2) Rbac.vue
p = r'..\frontend\src\views\Rbac.vue'
s = io.open(p, encoding='utf-8').read()

# 用户详情类型
s = s.replace('''<el-descriptions-item label="类型">{{ userDetail.userType || '—' }}</el-descriptions-item>''',
              '''<el-descriptions-item label="类型">{{ enumLabel('userType', userDetail.userType) }}</el-descriptions-item>''', 1)

# 模块字典补齐
s = s.replace("""  iam: '用户与权限', person: '人员与档案', biz: '业务办理', fin: '财务',
  asset: '资产房源', ops: '运维工单', msg: '消息待办', sys: '系统配置',
  rpt: '报表统计', open: '开放平台', gov: '监管报送', alloc: '配租轮候'""",
              """  iam: '用户与权限', person: '人员与档案', biz: '业务办理', fin: '财务',
  asset: '资产房源', ops: '运维工单', msg: '消息待办', sys: '系统配置',
  rpt: '报表统计', open: '开放平台', gov: '监管报送', alloc: '配租轮候',
  'access-records': '通行记录', auth: '认证会话', credit: '信用惩戒',
  credits: '信用惩戒', dev: '设备管理', files: '文件管理', grant: '通行授权',
  'grant-audit-logs': '授权审计', keyring: '钥匙管理', messages: '消息',
  orgs: '组织机构', platform: '平台管理', rbac: '用户与权限', rule: '计费规则',
  rules: '计费规则', 'short-rent-orders': '短租订单', test: '联调测试'""", 1)

# 在 MODULE_LABEL 后追加动作字典 + 展示函数
anchor = """  'short-rent-orders': '短租订单', test: '联调测试'
}"""
addition = """  'short-rent-orders': '短租订单', test: '联调测试'
}

/** 权限动作字典（按钮/接口级） */
const PERM_ACTION_LABEL = {
  list: '查看', query: '查询', detail: '详情', create: '新增', update: '修改',
  delete: '删除', assign: '授权', audit: '审核', approve: '审批', export: '导出',
  publish: '发布', disable: '停用', enable: '启用', manage: '管理', revoke: '撤销',
  print: '打印', view: '查看', edit: '编辑', handle: '处理', submit: '提交',
  cancel: '作废', sign: '签约', grant: '授权', scan: '扫描', recalc: '重算',
  freeze: '冻结', unfreeze: '解冻', run: '执行', sync: '同步', send: '发送',
  broadcast: '广播', batch: '批量', reset: '重置', unlock: '解锁', confirm: '确认',
  reject: '驳回', allocate: '核销', waive: '减免', verify: '核验', execute: '执行',
  complete: '完成', import: '导入', download: '下载', upload: '上传'
}

/** 页面权限显示名：优先路由标题，其次权限名 */
function routeTitle(p) {
  const path = String(p.routePath || '')
  if (path) {
    const r = router.getRoutes().find((x) => x.path === path)
    if (r && r.meta && r.meta.title) return r.meta.title
  }
  return String(p.permName || '').replace(/^页面-/, '')
}

/** 功能权限显示名：模块 · 动作，未知时回退权限名 */
function permLabel(p) {
  const parts = String(p.permCode || '').split(':')
  const mod = MODULE_LABEL[parts[0]]
  const act = PERM_ACTION_LABEL[parts[2]]
  if (mod && act) return mod + ' · ' + act
  if (act) return act
  return String(p.permName || p.permCode || '').replace(/^[a-z0-9-]+-/, '')
}"""
if anchor in s:
    s = s.replace(anchor, addition, 1)

# 路由实例
if 'const router = useRouter()' not in s:
    s = s.replace("import { useRoute, useRouter } from 'vue-router'",
                  "import { useRoute, useRouter } from 'vue-router'", 1)
    s = s.replace("const route = useRoute()", "const route = useRoute()\nconst router = useRouter()", 1)

# 页面权限 checkbox label
s = s.replace('''                    :label="p.permName"
                    :title="p.routePath || p.permCode"''',
              '''                    :label="routeTitle(p)"
                    :title="p.routePath || p.permCode"''', 1)

# 功能权限 checkbox label
s = s.replace('''                  :label="p.permName"
                  :title="p.permCode"''',
              '''                  :label="permLabel(p)"
                  :title="p.permCode"''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('rbac updated')
