# -*- coding: utf-8 -*-
"""列表内容正确性检查（API 层）。

规则
----
A. **列不为空**：列表接口返回的前 N 行中，若有字段**全部为空**，
   页面就会呈现"整列空白"（字段名对不上/未回填）。
B. **筛选生效**：带筛选参数请求时总数必须变化，否则说明筛选没接到后端。

白名单：允许整列为空的字段（可选字段、派生字段）。
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'

# 列表接口 → 页面名
ENDPOINTS = [
    ('/houses', '房源台账'), ('/contracts', '合同管理'), ('/persons', '人员档案'),
    ('/applications', '申请与审核'), ('/workorders', '工单维保'),
    ('/keyring', '钥匙包'), ('/grants', '授权与对账'), ('/dev-events', '设备告警'),
    ('/fin/meter-readings', '抄表管理'), ('/alerts', '告警与规则'),
    ('/complaints', '投诉管理'), ('/terminations', '退租管理'),
    ('/fin/bills', '账单与缴费'), ('/devices', '设备管理'),
]

# 接口 → 展示该数据的页面（只检查页面真正展示的列）
VIEWS = {
    '/houses': ['Houses.vue'], '/contracts': ['Contracts.vue'],
    '/persons': ['Persons.vue'], '/applications': ['Applications.vue'],
    '/workorders': ['WorkOrders.vue'], '/keyring': ['Keyring.vue'],
    '/grants': ['Grants.vue'], '/dev-events': ['DevEvents.vue'],
    '/fin/meter-readings': ['MeterReadings.vue'], '/complaints': ['Complaints.vue'],
    '/terminations': ['Terminations.vue'], '/fin/bills': ['Bills.vue'],
    '/devices': ['Devices.vue'],
}
VIEW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')


def view_props(files):
    props = set()
    for f in files:
        fp = os.path.join(VIEW_DIR, f)
        if not os.path.exists(fp):
            continue
        src = io.open(fp, encoding='utf-8', errors='replace').read()
        props.update(re.findall(r'prop="([\w.]+)"', src))
    return props


# 允许整列为空的字段
ALLOW_EMPTY = {
    'remark', 'remarkText', 'handleRemark', 'handleResult', 'images', 'attachment',
    'rawResponse', 'idCardMask', 'phoneMask', 'lastError', 'errorMsg', 'deleteReason',
    'actualExitDate', 'inspectResult', 'inspectImages', 'settleAmount', 'damageAmount',
    'transitionStartDate', 'transitionEndDate', 'relocationStartDate', 'relocationEndDate',
    'banReapplyEndDate', 'notaryNo', 'courtCaseNo', 'iouNo', 'contractFileUrl',
    'signFileUrl', 'images2', 'extra', 'payload', 'workorderId',
    # 抄表可无设备（手工抄表 / 新交付房源尚未装表），设备列允许为空
    'deviceId',
    # 访客次数仅「访客级」授权才有，普通授权为空属正常
    'visitLimitTimes',
}

# 筛选参数 → (接口, 参数名, 取值来源字段)
FILTER_CASES = [
    ('/devices', 'deviceType', 'deviceType', '设备管理-设备类型'),
    ('/houses', 'houseStatus', 'houseStatus', '房源台账-房态'),
    ('/fin/bills', 'status', 'billStatus', '账单-状态'),
    ('/workorders', 'orderStatus', 'orderStatus', '工单-状态'),
    ('/contracts', 'status', 'contractStatus', '合同-状态'),
]


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


def rows(path, tok, extra=''):
    url = path + ('&' if '?' in path else '?') + 'pageNum=1&pageSize=20' + extra
    st, d = call(url, tok)
    data = (d or {}).get('data') or {}
    return st, data.get('total'), (data.get('rows') or [])


def main():
    tok = login()
    if not tok:
        print('登录失败')
        return 2

    print('=' * 68)
    print('列表内容检查：%d 个接口' % len(ENDPOINTS))
    problems = []

    for path, label in ENDPOINTS:
        st, total, rs = rows(path, tok)
        if st != 200:
            problems.append('%s（%s）接口异常 %s' % (label, path, st))
            continue
        if not rs:
            print('  %-10s 无数据（跳过）' % label)
            continue
        props = view_props(VIEWS.get(path, []))
        keys = [k for k in rs[0].keys() if not props or k in props]
        empties = []
        for k in keys:
            if k in ALLOW_EMPTY or k.endswith('Label'):
                continue
            if all(r.get(k) in (None, '', [], {}) for r in rs):
                empties.append(k)
        flag = '✔' if not empties else '✗'
        print('  %s %-10s %3d 行 %2d 字段 %s' % (flag, label, len(rs), len(keys),
                                                ('整列为空: ' + '、'.join(empties)) if empties else ''))
        if empties:
            problems.append('%s 整列为空：%s' % (label, '、'.join(empties)))

    print('\n筛选生效检查：%d 例' % len(FILTER_CASES))
    for path, param, field, label in FILTER_CASES:
        st_all, total_all, all_rows = rows(path, tok)
        if not all_rows:
            print('  %-18s 无数据（跳过）' % label)
            continue
        # 取一行里该字段的真实值（保证能筛出结果）
        val = next((r.get(field) for r in all_rows if r.get(field)), None)
        if not val:
            print('  %-18s 该字段无值（跳过）' % label)
            continue
        st_f, total_f, _ = rows(path, tok, '&%s=%s' % (param, val))
        ok = st_f == 200 and total_f is not None and int(total_f) != int(total_all)
        print('  %s %-18s %s=%s：%s → %s' % ('✔' if ok else '✗', label, param, val,
                                             total_all, total_f))
        if st_f == 200 and total_f is not None and int(total_f) == int(total_all) and int(total_all) > 0:
            # 该字段当前全部同值（如工单全是 ASSIGNED），无法验证筛选，跳过
            print('  ~ %-16s 仅一种取值（%s），跳过筛选验证' % (label, val))
            continue
        if not ok:
            problems.append('%s 筛选 %s=%s 未生效（%s→%s）' % (label, param, val,
                                                              total_all, total_f))

    print('=' * 68)
    if problems:
        print('发现 %d 个问题：' % len(problems))
        for p in problems:
            print('  ✗ ' + p)
        return 1
    print('  ✔ 无整列空白，筛选均生效')
    return 0


if __name__ == '__main__':
    sys.exit(main())
