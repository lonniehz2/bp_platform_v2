# -*- coding: utf-8 -*-
"""账单列表支持按房源筛选 + 返回计费项名称（水电费账单可定位）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
F = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

# ---------- 1) 控制器：新增 houseId 参数 ----------
P = os.path.join(F, 'controller', 'BillingController.java')
s = io.open(P, encoding='utf-8').read()
if 'Long houseId' not in s:
    s = s.replace('''@RequestParam(required = false) Long personId,''',
                  '''@RequestParam(required = false) Long personId,
                                           @RequestParam(required = false) Long houseId,''', 1)
    s = s.replace('billingService.pageBills(pageNum, pageSize, orgId, contractId, personId,',
                  'billingService.pageBills(pageNum, pageSize, orgId, contractId, personId, houseId,', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('BillingController：已加 houseId')

# ---------- 2) 接口 ----------
P = os.path.join(F, 'service', 'BillingService.java')
s = io.open(P, encoding='utf-8').read()
if 'Long houseId' not in s:
    s = s.replace('PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId,',
                  'PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId,'
                  ' Long personId, Long houseId,', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('BillingService：已加 houseId')

# ---------- 3) 实现：过滤 + 计费项名称 ----------
P = os.path.join(F, 'service', 'impl', 'BillingServiceImpl.java')
s = io.open(P, encoding='utf-8').read()
if 'FinBill::getHouseId' not in s:
    s = s.replace('''    public PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId,''',
                  '''    public PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId,'''
                  ' Long personId,\n                                            Long houseId,', 1)
    s = s.replace('''                .eq(status != null && !status.isBlank(), FinBill::getBillStatus, status)''',
                  '''                .eq(status != null && !status.isBlank(), FinBill::getBillStatus, status)
                .eq(houseId != null, FinBill::getHouseId, houseId)''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('BillingServiceImpl：已加房源过滤')
else:
    print('BillingServiceImpl：已存在房源过滤')
