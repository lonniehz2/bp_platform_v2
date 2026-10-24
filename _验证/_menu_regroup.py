# -*- coding: utf-8 -*-
"""重构菜单：按业务域归为 8 组，并补上「设备告警」入口。

新分组：
  运营总览 / 保障对象 / 资格准入 / 合同管理 / 账务收费 /
  资产与设备 / 服务与监督 / 系统与集成
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
R = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')
M = os.path.join(ROOT, 'frontend', 'src', 'layout', 'useMenu.js')

# 路径 → 新分组
PATH_GROUP = {
    '/dashboard': '运营总览', '/todos': '运营总览', '/messages': '运营总览',
    '/persons': '保障对象', '/annual-reviews': '保障对象',
    '/applications': '资格准入', '/waitlist': '资格准入',
    '/allocations': '资格准入', '/publicities': '资格准入',
    '/contracts': '合同管理', '/contract-changes': '合同管理',
    '/exchanges': '合同管理', '/terminations': '合同管理',
    '/fee-items': '账务收费', '/bills': '账务收费', '/deposits': '账务收费',
    '/arrears': '账务收费', '/subsidies': '账务收费', '/cashflow': '账务收费',
    '/reports': '账务收费',
    '/houses': '资产与设备', '/spaces': '资产与设备',
    '/house-calendar': '资产与设备', '/short-rent': '资产与设备',
    '/devices': '资产与设备', '/dev-events': '资产与设备',
    '/access': '资产与设备', '/keyring': '资产与设备', '/grants': '资产与设备',
    '/workorders': '服务与监督', '/alerts': '服务与监督',
    '/complaints': '服务与监督', '/visits': '服务与监督',
    '/appeals': '服务与监督', '/credits': '服务与监督',
    '/orgs': '系统与集成', '/rbac': '系统与集成', '/sys': '系统与集成',
    '/ops-center': '系统与集成', '/ops-extras': '系统与集成',
    '/open': '系统与集成', '/gov': '系统与集成',
}

# ---------- 1) 路由：按路径改写 meta.group ----------
s = io.open(R, encoding='utf-8').read()
import re

def fix_block(match):
    block = match.group(0)
    pm = re.search(r"path:\s*'([^']+)'", block)
    if not pm:
        return block
    path = pm.group(1).split('/:')[0]
    group = PATH_GROUP.get(path)
    if not group:
        return block
    return re.sub(r"group:\s*'[^']+'", "group: '%s'" % group, block, count=1)

s = re.sub(r"\{\s*path:\s*'[^']+'[\s\S]{0,400}?meta:\s*\{[^}]*\}[\s\S]{0,80}?\}", fix_block, s)

# ---------- 2) 新增 /dev-events 路由 ----------
if '/dev-events' not in s:
    anchor = "    {\n      path: '/access',"
    route = ("    {\n      path: '/dev-events',\n"
             "      name: 'DevEvents',\n"
             "      component: () => import('@/views/DevEvents.vue'),\n"
             "      meta: { title: '设备告警', icon: 'Warning', group: '资产与设备' }\n"
             "    },\n")
    s = s.replace(anchor, route + anchor, 1)

io.open(R, 'w', encoding='utf-8', newline='').write(s)
print('router：分组已改写并新增 /dev-events')

# ---------- 3) useMenu：统一两套分组 ----------
t = io.open(M, encoding='utf-8').read()

NEW_ORDER = """export const GROUP_ORDER = [
  '运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
  '资产与设备', '服务与监督', '系统与集成'
]"""
t = re.sub(r"export const GROUP_ORDER = \[[\s\S]*?\]", NEW_ORDER, t, count=1)

NEW_ICON = """export const GROUP_ICON = {
  运营总览: 'DataBoard',
  保障对象: 'UserFilled',
  资格准入: 'Tickets',
  合同管理: 'Document',
  账务收费: 'Money',
  资产与设备: 'OfficeBuilding',
  服务与监督: 'Service',
  系统与集成: 'Setting'
}"""
t = re.sub(r"export const GROUP_ICON = \{[\s\S]*?\}", NEW_ICON, t, count=1)

NEW_CLASSIC_ORDER = """export const CLASSIC_ORDER = [
  '运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
  '资产与设备', '服务与监督', '系统与集成'
]"""
t = re.sub(r"export const CLASSIC_ORDER = \[[\s\S]*?\]", NEW_CLASSIC_ORDER, t, count=1)

NEW_CLASSIC_ICON = """export const CLASSIC_ICON = {
  运营总览: 'DataBoard',
  保障对象: 'UserFilled',
  资格准入: 'Tickets',
  合同管理: 'Document',
  账务收费: 'Money',
  资产与设备: 'OfficeBuilding',
  服务与监督: 'Service',
  系统与集成: 'Setting'
}"""
t = re.sub(r"export const CLASSIC_ICON = \{[\s\S]*?\}", NEW_CLASSIC_ICON, t, count=1)

# CLASSIC_GROUP 重写
lines = ['/** 路径 → 风格1 分组 */', 'const CLASSIC_GROUP = {']
groups = {}
for path, g in PATH_GROUP.items():
    groups.setdefault(g, []).append(path)
for g in ['运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
          '资产与设备', '服务与监督', '系统与集成']:
    items = groups.get(g, [])
    lines.append('  ' + ', '.join("'%s': '%s'" % (p, g) for p in items) + ',')
lines.append('}')
t = re.sub(r"/\*\* 路径 → 风格1 分组 \*/\nconst CLASSIC_GROUP = \{[\s\S]*?\n\}", '\n'.join(lines), t, count=1)

# 别名表：旧名映射到新名（兼容历史 meta）
NEW_ALIAS = """const GROUP_ALIAS = {
  仪表盘: '运营总览',
  会员: '保障对象',
  线索: '资格准入',
  合同: '合同管理',
  财务: '账务收费',
  房源: '资产与设备',
  授权与交房: '资产与设备',
  资产台账: '资产与设备',
  管理后台: '系统与集成',
  退出与监督: '服务与监督',
  更多: '服务与监督'
}"""
t = re.sub(r"const GROUP_ALIAS = \{[\s\S]*?\}", NEW_ALIAS, t, count=1)

io.open(M, 'w', encoding='utf-8', newline='').write(t)
print('useMenu：分组与图标已统一为 8 组')
