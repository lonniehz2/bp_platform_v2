# -*- coding: utf-8 -*-
"""导出 P0 读写操作的 DTO 字段（契约写入/收款/押金/退款/合同/年审等）"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
OUT = r'D:\Work\业务平台开发\_验证\_p0_dto_spec.json'

WANT = [
    # 合同
    'ContractCreateCmd', 'ContractSignCmd', 'ContractRenewCmd', 'ContractTerminateCmd',
    # 账户/收款/出账
    'PaymentCreateCmd', 'BillGenerateCmd', 'BillGenerateBatchCmd', 'BillWaiveCmd',
    'PayAllocateCmd',
    # 押金/退款
    'DepositCreateCmd', 'RefundCreateCmd', 'RefundApproveCmd',
    # 退租
    'TerminationCreateCmd', 'TerminationApproveCmd',
    # 公示/配租
    'PublicityCreateCmd', 'LotteryCmd', 'GiveUpCmd', 'AllocationSignCmd',
    # 年审
    'AnnualReviewCreateCmd', 'AnnualReviewReviewCmd', 'AnnualReviewBatchCmd',
    # 催缴/补贴
    'DunningCreateCmd', 'SubsidyCalcCmd', 'SubsidyBatchCmd',
]

found = {}
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        m = re.search(r'record\s+(\w+)\s*\((.*?)\)\s*\{', s, re.S)
        if not m or m.group(1) not in WANT:
            continue
        name = m.group(1)
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        parts = []
        for ln in body.split('\n'):
            t = ln.strip().rstrip(',')
            if not t or t.startswith('@') or t.startswith('//'):
                continue
            t = re.sub(r'^@\w+(\([^)]*\))?\s*', '', t)
            if ' ' in t:
                parts.append(t)
        req = []
        if '@NotNull' in m.group(2) or '@NotBlank' in m.group(2):
            req.append('has_required')
        found[name] = {'file': f, 'fields': parts, 'required_hint': bool(req)}

import json
json.dump(found, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('找到 %d / %d 个 DTO\n' % (len(found), len(WANT)))
for n in WANT:
    if n in found:
        f = found[n]
        print('■ %s (%d)' % (n, len(f['fields'])))
        for x in f['fields']:
            print('    ' + x)
    else:
        print('□ %s  ← 未找到（需确认接口是否有独立 DTO）' % n)
    print()
