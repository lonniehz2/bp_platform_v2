# -*- coding: utf-8 -*-
"""① 空间页改为组织下拉+自动加载 ② 造一套完整 5 层演示数据"""
import io
import json
import os
import urllib.error
import urllib.request

# ============ ① 前端：组织下拉 + 自动加载 ============
P = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'
s = io.open(P, encoding='utf-8').read()

old_bar = '''      <el-input v-model.number="orgId" placeholder="组织ID（可空）"
                style="width:170px" @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>'''
new_bar = '''      <el-select v-model="orgId" placeholder="选择组织（自动加载）"
                 filterable style="width:230px" @change="load">
        <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="o.id" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>'''
if old_bar in s:
    s = s.replace(old_bar, new_bar, 1)
    print('  ✓ Spaces.vue：组织ID输入改为下拉')

# 脚本：加载组织列表 + 默认选第一个
s = s.replace("const expandAll = ref(true)",
              "const expandAll = ref(true)\nconst orgs = ref([])", 1)

s = s.replace('''onMounted(() => { /* 需先输入组织ID */ })''',
              '''/** 加载可选的根组织；默认选第一个并直接展示空间树 */
async function loadOrgs() {
  try {
    const d = await orgApi.children()
    orgs.value = Array.isArray(d) ? d : (d.rows || [])
    if (!orgId.value && orgs.value.length) {
      // 优先选名称含「演示」的组织，便于验收
      const demo = orgs.value.find((o) => (o.orgName || '').includes('演示'))
      orgId.value = (demo || orgs.value[0]).id
    }
    if (orgId.value) await load()
  } catch (e) { orgs.value = [] }
}

onMounted(loadOrgs)''', 1)

# 提示文案更新
s = s.replace('title="后端只提供树形接口（/spaces/tree），无分页列表；path_code 每级 2 位"',
              'title="选择组织后自动加载空间树；层级：片区/楼栋 → 单元 → 楼层 → 房间 → 床位/车位"')

# 补 orgApi import
if "import { spaceApi } from '@/api/modules'" in s and 'orgApi' not in s:
    s = s.replace("import { spaceApi } from '@/api/modules'",
                  "import { spaceApi, orgApi } from '@/api/modules'", 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ Spaces.vue：自动加载组织与空间树')

# ============ ② 造演示数据 ============
BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))


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

# 找/建一个「演示」组织作为根
st, r = call('GET', '/api/v1/orgs/children', None, TOK)
orgs = r.get('data') or []
demo = next((o for o in orgs if '演示' in (o.get('orgName') or '')), None)
if demo:
    ORG = demo['id']
    print('\n复用演示组织：%s (%s)' % (demo['orgName'], ORG))
else:
    st, r = call('POST', '/api/v1/orgs', {
        'orgCode': 'DEMO', 'orgName': '演示小区（空间样例）',
        'orgType': 'COMMUNITY', 'sortNo': 0, 'remark': '空间层级演示数据'}, TOK)
    ORG = (r.get('data') or {}).get('id')
    print('\n新建演示组织：%s (%s) %s' % (r.get('code'), ORG,
                                        str(r.get('message'))[:40]))

created = {'org': ORG, 'buildings': [], 'units': [], 'floors': [],
           'rooms': [], 'beds': [], 'parking': []}


def mk(code, name, stype, parent, area=None, sort=1):
    body = {'orgId': ORG, 'spaceCode': code, 'spaceName': name,
            'spaceType': stype, 'sortNo': sort}
    if parent:
        body['parentId'] = parent
    if area:
        body['area'] = area
    st, r = call('POST', '/api/v1/spaces', body, TOK)
    sid = (r.get('data') or {}).get('id')
    if r.get('code') != 'BP00000':
        print('    ✗ %s %s %s' % (code, r.get('code'), str(r.get('message'))[:40]))
    return sid


print('\n— 楼栋 / 单元 / 楼层 / 房间 / 床位 / 车位 —')
n_err = 0
for bi, bname in enumerate(('A栋', 'B栋'), 1):
    b = mk('DEMO-B%d' % bi, bname, 'BUILDING', None, sort=bi)
    if not b:
        n_err += 1
        continue
    created['buildings'].append(b)
    for ui in (1, 2):
        u = mk('DEMO-B%d-U%d' % (bi, ui), '%d单元' % ui, 'UNIT', b)
        if not u:
            n_err += 1
            continue
        created['units'].append(u)
        for fi in (1, 2, 3):
            f = mk('DEMO-B%d-U%d-F%d' % (bi, ui, fi), '%d层' % fi, 'FLOOR', u)
            if not f:
                n_err += 1
                continue
            created['floors'].append(f)
            for ri in (1, 2, 3, 4):
                rc = 'DEMO-B%d-U%d-F%d-R%02d' % (bi, ui, fi, ri)
                rname = '%d0%d' % (fi, ri)
                room = mk(rc, rname, 'ROOM', f, area=60 + ri * 5, sort=ri)
                if not room:
                    n_err += 1
                    continue
                created['rooms'].append(room)
                # 每层第 1 个房间下放 2 个床位（演示房源细分场景）
                if ri == 1:
                    for bed in (1, 2):
                        bd = mk(rc + '-BED%d' % bed, '%s-%d号床' % (rname, bed),
                                'BED', room, sort=bed)
                        if bd:
                            created['beds'].append(bd)

# 车位区 + 车位（悬挂在楼栋 A 下，演示非住宅业态）
if created['buildings']:
    pk = mk('DEMO-PARK', '地下车库', 'GARAGE', created['buildings'][0])
    if pk:
        created['parking'].append(pk)
        for i in range(1, 7):
            p = mk('DEMO-PARK-P%02d' % i, '车位%02d' % i, 'PARKING', pk, sort=i)
            if p:
                created['parking'].append(p)

D['demoOrgId'] = ORG
json.dump(D, open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)

print('\n汇总：楼栋 %d ｜ 单元 %d ｜ 楼层 %d ｜ 房间 %d ｜ 床位 %d ｜ 车位区+车位 %d ｜ 失败 %d'
      % (len(created['buildings']), len(created['units']), len(created['floors']),
         len(created['rooms']), len(created['beds']), len(created['parking']),
         n_err))
print('演示组织ID：%s' % ORG)
