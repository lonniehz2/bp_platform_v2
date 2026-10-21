# -*- coding: utf-8 -*-
"""显示层一致性检查（可复用于每次回归）

解决的问题（这轮反复出现的同一类缺陷）：
  ① 界面上出现英文枚举编码，如 ALLOCATED / PUBLIC_RENTAL
  ② 界面上出现裸 ID，如 personId=370832686538952704
  ③ 详情里出现英文字段名，如 unpaidAmount / standardId
  ④ 树形接口层级不成立或子节点未补中文

用法：
  python _check_display.py            # 报告问题
  python _check_display.py --strict   # 有任何问题即返回非 0（CI/验收用）

退出码：0 通过；1 发现问题；2 环境不可达
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = os.environ.get('BP_BASE', 'http://192.168.31.11:8080')
TENANT = os.environ.get('BP_TENANT', '350600')
USER = os.environ.get('BP_USER', 'admin')
PWD = os.environ.get('BP_PWD', 'admin123')

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.abspath(os.path.join(HERE, '..', 'frontend', 'src'))
STRICT = '--strict' in sys.argv

ENUM_SUFFIX = re.compile(
    r'(Status|Type|Stage|Mode|Level|Channel|Result|Source|Kind|Category)$')
ID_SUFFIX = re.compile(r'Id$')
SKIP_KEYS = {'id', 'tenantId'}

LIST_ENDPOINTS = [
    '/applications', '/contracts', '/contract-changes', '/allocation/batches',
    '/allocation/allocations', '/allocation/waiting', '/annual-reviews',
    '/terminations', '/fin/bills', '/fin/payments', '/fin/deposits',
    '/fin/refunds', '/fin/subsidies/records', '/fin/dunnings', '/fin/cash-flows',
    '/fin/fee-items', '/workorders', '/alerts', '/complaints', '/appeals',
    '/credits', '/exchanges', '/visits', '/short-rent-orders', '/access-records',
    '/keyring', '/grants', '/publicities', '/devices', '/orgs', '/houses',
    '/persons', '/house-calendar', '/fin/reconciles',
]

DETAIL_ENDPOINTS = [
    '/short-rent-orders', '/applications', '/contracts', '/fin/bills',
    '/fin/payments', '/fin/deposits', '/fin/refunds', '/workorders',
    '/terminations', '/annual-reviews', '/alerts', '/appeals', '/credits',
    '/exchanges', '/complaints', '/visits', '/keyring', '/grants',
    '/publicities', '/devices', '/persons', '/houses',
]

TOK = None


def call(method, path, body=None):
    headers = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        headers['Authorization'] = 'Bearer ' + TOK
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


def load_frontend_dicts():
    """读取前端静态字典（字段名 + 枚举值）"""
    fields, enums = set(), set()
    fp = os.path.join(FRONTEND, 'constants', 'fieldLabels.js')
    if os.path.exists(fp):
        s = io.open(fp, encoding='utf-8').read()
        fields = set(re.findall(r"^\s{2}(\w+):\s*['\"]", s, re.M))
    ep = os.path.join(FRONTEND, 'constants', 'enums.js')
    if os.path.exists(ep):
        s = io.open(ep, encoding='utf-8').read()
        enums = set(re.findall(r"^\s*'?([A-Z][A-Z_0-9]*)'?:\s*'", s, re.M))
    return fields, enums


def rows_of(path, size=20):
    sep = '&' if '?' in path else '?'
    data = call('GET', '/api/v1%s%spageNum=1&pageSize=%d' % (path, sep, size)).get('data')
    if isinstance(data, dict):
        return data.get('rows') or []
    return data if isinstance(data, list) else []


def main():
    global TOK
    login = call('POST', '/api/v1/auth/login',
                 {'tenantId': TENANT, 'username': USER, 'password': PWD})
    TOK = (login.get('data') or {}).get('token')
    if not TOK:
        print('✗ 无法登录（%s）：%s' % (BASE, login.get('code')))
        return 2

    labels = call('GET', '/api/v1/sys/field-labels').get('data') or {}
    static_fields, static_enums = load_frontend_dicts()

    print('=' * 76)
    print(' 显示层一致性检查  %s' % BASE)
    print('=' * 76)
    print(' 字段字典：远程 %d ｜ 静态 %d' % (len(labels), len(static_fields)))
    print(' 枚举字典：静态 %d' % len(static_enums))

    problems = []

    # ---------- ① 字段中文名 ----------
    miss_field = {}
    seen_keys = set()

    def scan(row, where):
        if not isinstance(row, dict):
            return
        for k in row:
            if k.endswith(('Label', 'Name')) or k in SKIP_KEYS:
                continue
            seen_keys.add(k)
            if k not in labels and k not in static_fields:
                # xxxId 可由基础名推导
                m = re.match(r'^(\w+?)Id$', k)
                if m and (m.group(1) in labels or m.group(1) in static_fields):
                    continue
                miss_field.setdefault(k, set()).add(where)

    for p in LIST_ENDPOINTS:
        for r in rows_of(p):
            scan(r, p.split('/')[-1])
    for p in DETAIL_ENDPOINTS:
        rs = rows_of(p, 3)
        for r in rs:
            if not isinstance(r, dict) or not r.get('id'):
                continue
            d = call('GET', '/api/v1%s/%s' % (p, r['id'])).get('data')
            scan(d, p.split('/')[-1] + '/详情')

    if miss_field:
        problems.append('① 字段无中文名 %d 个' % len(miss_field))
        for k in sorted(miss_field):
            problems.append('     %-24s %s' % (k, ', '.join(sorted(miss_field[k]))[:56]))
    else:
        problems.append('① 字段中文名：✔ 全部覆盖（%d 个字段）' % len(seen_keys))

    # ---------- ② 枚举中文 ----------
    miss_enum = {}
    for p in LIST_ENDPOINTS:
        for row in rows_of(p, 5):
            if not isinstance(row, dict):
                continue
            for k, v in row.items():
                if ENUM_SUFFIX.search(k) and k + 'Label' not in row \
                        and isinstance(v, str) and re.fullmatch(r'[A-Z][A-Z_0-9]+', v):
                    if v not in static_enums:
                        miss_enum.setdefault(v, set()).add(k)

    if miss_enum:
        problems.append('② 枚举无中文 %d 个' % len(miss_enum))
        for k in sorted(miss_enum):
            problems.append('     %-22s %s' % (k, ', '.join(sorted(miss_enum[k]))[:56]))
    else:
        problems.append('② 枚举中文：✔ 无遗漏')

    # ---------- ③ 裸 ID ----------
    miss_id = {}
    for p in LIST_ENDPOINTS:
        for row in rows_of(p, 5):
            if not isinstance(row, dict):
                continue
            for k, v in row.items():
                if ID_SUFFIX.search(k) and k + 'Name' not in row \
                        and v not in (None, '', 'None'):
                    miss_id.setdefault(k, set()).add(p.split('/')[-1])

    # 说明：这些 ID 业务上不需要名称（审计人、内部引用等）
    # 这些 ID 在业务语义上**不需要**额外名称：
    #   approveById/decideUserId/handleUserId/operatorId/assignUserId → 内部操作人
    #   bizId/sourceId/eventId → 弱引用或本身就是可读编号
    #   tenantId → 租户号（350600），可读
    #   parentId → 上级节点（树形里已体现）
    #   deviceId → 设备自身编号（devices 列表里就是主键，无冗余名称）
    ID_ALLOW = {'approveById', 'decideUserId', 'handleUserId', 'operatorId',
                'bizId', 'sourceId', 'eventId', 'tenantId', 'assignUserId',
                'createBy', 'updateBy', 'parentId', 'deviceId'}
    real_miss = {k: v for k, v in miss_id.items() if k not in ID_ALLOW}

    if real_miss:
        problems.append('③ ID 无名称 %d 个' % len(real_miss))
        for k in sorted(real_miss):
            problems.append('     %-20s %s' % (k, ', '.join(sorted(real_miss[k]))[:56]))
    else:
        problems.append('③ ID 名称：✔ 无遗漏（%d 个允许项除外）' % len(ID_ALLOW & set(miss_id)))

    # ---------- ④ 树形结构 ----------
    org_roots = call('GET', '/api/v1/orgs/children').get('data') or []
    multi = sum(1 for n in org_roots
                if (call('GET', '/api/v1/orgs/children?parentId=%s' % n['id'])
                    .get('data') or []))
    if len(org_roots) and multi == 0:
        problems.append('④ 组织结构：⚠ 全部为根节点（无父子关系，树形退化为列表）')
    else:
        problems.append('④ 组织结构：✔ %d 个根 / %d 个含子节点' % (len(org_roots), multi))

    space_ok = '?'
    cfg = os.path.join(HERE, '_test_data.json')
    if os.path.exists(cfg):
        org = json.load(io.open(cfg, encoding='utf-8')).get('orgId')
        if org:
            tree = call('GET', '/api/v1/spaces/tree?orgId=%s' % org).get('data') or []
            with_children = sum(1 for n in tree if n.get('children'))
            labels_ok = all(
                n.get('spaceTypeLabel')
                for n in tree
            ) if tree else False
            space_ok = '✔ %d 根 / %d 含子 / 类型中文 %s' % (
                len(tree), with_children, '是' if labels_ok else '否')
            if tree and not labels_ok:
                problems.append('④ 空间树：⚠ 顶层 spaceTypeLabel 缺失')

    # ---------- 输出 ----------
    bad = [p for p in problems if '✔' not in p]
    for line in problems:
        print(' ' + line)
    print('-' * 76)
    print(' 空间树：%s' % space_ok)
    if bad:
        print(' 结论：发现 %d 类问题' % len(bad))
        return 1
    print(' 结论：✔ 显示层一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
