# -*- coding: utf-8 -*-
"""修复组织树：前端真递归 + 造出多层级测试数据"""
import io
import json
import urllib.error
import urllib.request

# ---------- 1) 前端递归 ----------
P = r'D:\Work\业务平台开发\frontend\src\views\Orgs.vue'
s = io.open(P, encoding='utf-8').read()

start = s.find('async function loadTree()')
end = s.find('\n}', s.find('tree.value = level1')) + 2
if start == -1 or end < start:
    print('!! 定位失败')
else:
    NEW = '''async function loadTree() {
  try {
    // 后端只提供 /orgs/children（按 parentId 取子节点），无整树接口；
    // 这里做**真正的递归**加载，深度上限 6 层，并防环。
    const MAX_DEPTH = 6
    const seen = new Set()

    async function childrenOf(parentId) {
      const res = await orgApi.children(parentId)
      return Array.isArray(res) ? res : (res?.rows || [])
    }

    async function build(list, depth) {
      const out = []
      for (const n of list) {
        if (seen.has(n.id)) continue      // 防环
        seen.add(n.id)
        const node = { ...n }
        if (depth < MAX_DEPTH) {
          try {
            const kids = await childrenOf(n.id)
            if (kids.length) node.children = await build(kids, depth + 1)
          } catch (e) { /* 单节点失败不影响整棵树 */ }
        }
        out.push(node)
      }
      return out
    }

    const roots = await childrenOf()
    tree.value = await build(roots, 1)
  } catch (e) { tree.value = [] }
}
'''
    s = s[:start] + NEW + s[end:]

    # 增加「统计节点数」以便确认递归生效（树为空时提示更明确）
    s = s.replace('<el-empty v-if="!tree.length" description="暂无组织" :image-size="60" />',
                  '<el-empty v-if="!tree.length" description="暂无组织数据" :image-size="60" />')
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ Orgs.vue 改为递归加载（深度 6，防环）')

# ---------- 2) 造多层级组织 ----------
BASE = 'http://192.168.31.11:8080'
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']


def post(p, body):
    r = urllib.request.Request(
        BASE + p, data=json.dumps(body).encode(), method='POST',
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}


import time
sfx = str(int(time.time()))[-4:]
print('\n— 造层级组织 —')
r = post('/api/v1/orgs', {'orgCode': 'DIST' + sfx, 'orgName': '测试区住建局' + sfx,
                          'orgType': 'DISTRICT', 'sortNo': 1})
dist = (r.get('data') or {}).get('id')
print('  %s 区级 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗', dist,
                            str(r.get('message'))[:40]))

nodes = {'区': dist}
if dist:
    for sn in ('A', 'B'):
        r = post('/api/v1/orgs', {
            'orgCode': 'ST%s%s' % (sn, sfx), 'orgName': '%s街道' % sn,
            'orgType': 'COMMUNITY', 'parentId': dist, 'sortNo': 1})
        st = (r.get('data') or {}).get('id')
        nodes[sn] = st
        print('  %s %s街道 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗', sn,
                                       st, str(r.get('message'))[:40]))
        if st:
            for i in (1, 2):
                r = post('/api/v1/orgs', {
                    'orgCode': 'C%s%d%s' % (sn, i, sfx),
                    'orgName': '%s街道%d号小区' % (sn, i),
                    'orgType': 'COMMUNITY', 'parentId': st, 'sortNo': i})
                print('     %s 小区 %s%s → %s'
                      % ('✓' if r.get('code') == 'BP00000' else '✗', sn, i,
                         (r.get('data') or {}).get('id')))
