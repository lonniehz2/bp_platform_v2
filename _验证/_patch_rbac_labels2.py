# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\views\Rbac.vue'
s = io.open(p, encoding='utf-8').read()

anchor = """  rules: '计费规则', 'short-rent-orders': '短租订单', test: '联调测试'
}
"""
addition = """  rules: '计费规则', 'short-rent-orders': '短租订单', test: '联调测试'
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

/** 页面权限显示名：优先路由标题 */
function routeTitle(p) {
  const path = String(p.routePath || '')
  if (path) {
    const r = router.getRoutes().find((x) => x.path === path)
    if (r && r.meta && r.meta.title) return r.meta.title
  }
  return String(p.permName || '').replace(/^页面-/, '')
}

/** 功能权限显示名：模块 · 动作 */
function permLabel(p) {
  const parts = String(p.permCode || '').split(':')
  const mod = MODULE_LABEL[parts[0]]
  const act = PERM_ACTION_LABEL[parts[2]]
  if (mod && act) return mod + ' · ' + act
  if (act) return act
  return String(p.permName || p.permCode || '').replace(/^[a-z0-9-]+-/, '')
}
"""
if 'function permLabel' not in s:
    s = s.replace(anchor, addition, 1)

# 页面权限标签
s = s.replace('''                    :label="p.permName"
                    :title="p.routePath || p.permCode"''',
              '''                    :label="routeTitle(p)"
                    :title="p.routePath || p.permCode"''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('functions inserted')
