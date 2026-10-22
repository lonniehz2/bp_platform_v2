# -*- coding: utf-8 -*-
"""校验：源码里 @RequirePerm 引用的权限码是否都已在库中存在（缺失则创建）。"""
import io
import json
import os
import re
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
API = 'http://192.168.31.11:8080/api/v1'
CN = {'view': '查看', 'create': '新建', 'update': '编辑', 'delete': '删除', 'export': '导出',
      'import': '导入', 'audit': '审核', 'approve': '审批', 'sign': '签约', 'renew': '续签',
      'terminate': '终止', 'change': '变更', 'transfer': '换房', 'execute': '执行',
      'status': '状态变更', 'verify': '核验', 'judge': '资格判定', 'assign': '分配',
      'grant': '授权', 'revoke': '撤销', 'reset': '重置', 'issue': '出账', 'cancel': '作废',
      'pay': '核销', 'refund': '退款', 'deduct': '抵扣', 'calc': '计算', 'dunning': '催缴',
      'handle': '处理', 'close': '结单', 'read': '标记已读', 'done': '办结', 'record': '登记',
      'submit': '报送', 'roll': '摇号', 'recalc': '重算', 'batch': '批次管理',
      'publish': '发布', 'scan': '扫描', 'sync': '同步', 'send': '发送', 'run': '执行',
      'freeze': '冻结', 'unfreeze': '解冻', 'query': '查询', 'detail': '详情', 'list': '列表',
      'broadcast': '广播'}


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', '350600')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return {'code': 'HTTP%d' % e.code}


def main():
    token = call('/auth/login', 'POST',
                 {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
    have = {p['permCode'] for p in call('/rbac/permissions', token=token)['data']}

    used = set()
    for dirpath, _, files in os.walk(JAVA):
        for fn in files:
            if not fn.endswith('Controller.java'):
                continue
            s = io.open(os.path.join(dirpath, fn), encoding='utf-8').read()
            for m in re.finditer(r'@(?:com\.yundao\.bp\.iam\.security\.)?RequirePerm\("([^"]+)"\)', s):
                used.add(m.group(1))
    missing = sorted(used - have)
    print('源码引用权限码 %d 个，库中缺失 %d 个' % (len(used), len(missing)))
    created = 0
    for code in missing:
        parts = code.split(':')
        act = parts[-1] if parts else code
        name = '%s-%s' % (parts[-2] if len(parts) > 1 else code, CN.get(act, act))
        r = call('/rbac/permissions', 'POST',
                 {'permCode': code, 'permName': name, 'permType': 'BUTTON', 'sortNo': 0}, token)
        if r.get('code') == 'BP00000':
            created += 1
        else:
            print('  失败 %s -> %s' % (code, r.get('code')))
    print('已补建 %d 个' % created)
    if missing:
        print('缺失样例:', missing[:8])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
