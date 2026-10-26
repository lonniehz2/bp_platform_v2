# -*- coding: utf-8 -*-
"""筛选全量覆盖检查：每个列表页至少要有 1 个筛选项真正生效。

做法
----
对每个列表接口：
1. 取 20 行数据；
2. 找出"枚举型字段"（值为 A-Z_ 常量）作为候选筛选；
3. 依次用 `字段名=值` 请求，若总数变化 → 该筛选生效；
4. 全部候选都不变 → 判该页"无有效筛选"。

这样能自动发现两类问题：
* 前端传的键后端不认（如 billStatus vs status）；
* 后端接了参数但没真正过滤。
"""
import json
import sys
import urllib.parse
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'

# 接口 → 页面名（覆盖主要列表页）
ENDPOINTS = [
    ('/houses', '房源台账'),
    ('/contracts', '合同管理'),
    ('/persons', '人员档案'),
    ('/applications', '申请与审核'),
    ('/workorders', '工单维保'),
    ('/complaints', '投诉管理'),
    ('/terminations', '退租管理'),
    ('/exchanges', '换房管理'),
    ('/annual-reviews', '年审复核'),
    ('/allocation/waiting', '轮候管理'),
    ('/publicities', '公示管理'),
    ('/fin/bills', '账单与缴费'),
    ('/fin/fee-items', '计费项目'),
    ('/fin/deposits', '押金与退款'),
    ('/fin/subsidies/records', '补贴管理'),
    ('/keyring', '钥匙包'),
    ('/grants', '通行授权'),
    ('/devices', '设备管理'),
    ('/dev-events', '设备告警'),
    ('/alerts', '告警处理'),
    ('/visits', '入户走访'),
    ('/short-rent-orders', '短租订单'),
    ('/access-records', '通行记录'),
    ('/credits', '信用惩戒'),
    ('/orgs', '组织机构'),
]

# 这些字段不作为筛选候选（展示用/敏感）
SKIP_FIELDS = {'id', 'tenantId', 'createTime', 'updateTime', 'billNo', 'orderNo'}


def call(path, tok=None, body=None, method='GET'):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception:
        return 0, {}


def login(u='admin', p='admin123'):
    st, d = call('/auth/login', body={'tenantCode': TENANT, 'username': u,
                                      'password': p}, method='POST')
    return ((d or {}).get('data') or {}).get('token')


def fetch(path, tok, extra='', size=20, page=1):
    url = path + ('&' if '?' in path else '?') + 'pageNum=%d&pageSize=%d' % (page, size) + extra
    st, d = call(url, tok)
    data = (d or {}).get('data') or {}
    return st, data.get('total'), (data.get('rows') or [])


# 字段名 → 后端参数别名（很多控制器统一用 status/type/level）
ALIASES = {
    'Status': ['status', '{}Status'],
    'Type': ['type', '{}Type'],
    'Level': ['level', '{}Level'],
    'Category': ['category', '{}Category'],
    'Mode': ['mode', '{}Mode'],
}


def param_candidates(field):
    "字段可能的查询参数名（含常见别名）。"
    out = [field]
    for suffix, names in ALIASES.items():
        if field.endswith(suffix):
            base = field[:-len(suffix)]
            for n in names:
                out.append(n.format(base) if '{}' in n else n)
    # 去重保序
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


# 优先用「类型/状态」这类枚举筛选（比 deviceId 更有业务意义）
PREFER = ('Type', 'Status', 'Level', 'Category', 'Mode', 'Channel', 'Source')


def enum_fields(rows):
    """找出枚举型字段：值为全大写常量，且**至少有 2 个不同取值**。"""
    out = []
    sample = rows[0] if rows else {}
    for k, v in sample.items():
        if k in SKIP_FIELDS or k.endswith('Label') or not isinstance(v, str):
            continue
        if not (v and v.replace('_', '').isalpha() and v.upper() == v and len(v) > 2):
            continue
        distinct = {r.get(k) for r in rows if r.get(k)}
        if len(distinct) >= 2:
            out.append(k)
    out.sort(key=lambda f: (0 if f.endswith(PREFER) else 1, f))
    return out


def try_id_filters(path, tok, total, rows):
    """兜底：用外键过滤（personId/houseId/contractId/deviceId/orgId）。"""
    for field in ('personId', 'houseId', 'contractId', 'deviceId', 'orgId',
                  'planId', 'standardId', 'feeItemId'):
        val = next((r.get(field) for r in rows if r.get(field)), None)
        if not val:
            continue
        st, t, _ = fetch(path, tok, '&%s=%s' % (field, val))
        if st == 200 and t is not None and int(t) != int(total):
            return (field, val, total, t)
    return None


def try_keyword(path, tok, total, rows):
    """通用兜底：用首行的名称/编号片段做 keyword 搜索，总数应减少。"""
    for field in ('houseName', 'personName', 'title', 'itemName', 'orgName',
                  'deviceName', 'billNo', 'orderNo', 'contractNo'):
        val = next((r.get(field) for r in rows if isinstance(r.get(field), str)), None)
        if not val or len(val) < 3:
            continue
        frag = val[:4]
        st, t, _ = fetch(path, tok, '&keyword=' + urllib.parse.quote(frag))
        if st == 200 and t is not None and int(t) != int(total):
            return ('keyword', frag, total, t)
    return None


def main():
    tok = login()
    if not tok:
        print('登录失败')
        return 2

    print('=' * 72)
    print('筛选全量覆盖检查：%d 个列表接口' % len(ENDPOINTS))
    problems, no_filter, ok = [], [], 0

    for path, label in ENDPOINTS:
        st, total, rows = fetch(path, tok)
        # 采样多页（前 3 页 × 100）用于发现多值枚举，避免首页同质化
        sample_rows = []
        last_pg = max(1, int(int(total or 0) / 100))
        for pg in (1, 2, last_pg):
            _, _, part = fetch(path, tok, size=100, page=pg)
            sample_rows.extend(part)
        if sample_rows:
            rows_for_enum = sample_rows
        else:
            rows_for_enum = rows
        if st != 200:
            problems.append('%s（%s）接口异常 %s' % (label, path, st))
            continue
        if not rows:
            print('  - %-12s 无数据（跳过）' % label)
            continue

        worked = None
        tried = []
        for field in enum_fields(rows_for_enum)[:8]:
            val = next((r.get(field) for r in rows_for_enum if r.get(field)), None)
            if not val:
                continue
            for param in param_candidates(field):
                st2, t2, _ = fetch(path, tok, '&%s=%s' % (param, val))
                if t2 is None:
                    continue
                tried.append('%s=%s(%s)' % (param, val, t2))
                if st2 == 200 and int(t2) != int(total):
                    worked = (param, val, total, t2)
                    break

        if not worked:
            worked = try_id_filters(path, tok, total, rows)
        if not worked:
            worked = try_keyword(path, tok, total, rows)

        if worked:
            ok += 1
            print('  ✔ %-12s %s=%s：%s → %s' % (label, worked[0], worked[1],
                                                worked[2], worked[3]))
        else:
            no_filter.append(label)
            print('  ✗ %-12s 无有效筛选（试过：%s）' % (label, '、'.join(tried) or '无枚举字段'))

    print('=' * 72)
    print('有有效筛选 %d 页 / 无有效筛选 %d 页 / 异常 %d 个'
          % (ok, len(no_filter), len(problems)))
    if problems:
        for p in problems:
            print('  ✗ ' + p)
    if no_filter:
        print('  无有效筛选页面：' + '、'.join(no_filter))
    print('=' * 72)
    return 0 if (not problems and not no_filter) else 1


if __name__ == '__main__':
    sys.exit(main())
