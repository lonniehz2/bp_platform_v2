# -*- coding: utf-8 -*-
"""补 allocationApi 缺失方法（用文件方式，避免 shell 引号问题）"""
import io

P = r'D:\Work\业务平台开发\frontend\src\api\modules.js'
s = io.open(P, encoding='utf-8').read()

if 'setBatchStatus' in s:
    print('已存在，跳过')
else:
    anchor = "  sign: (id, data) => req.post(`/allocation/allocations/${id}/sign`, data),"
    add = anchor + '''
  setBatchStatus: (id, batchStatus) =>
    req.post(`/allocation/batches/${id}/status`, { batchStatus }),
  giveUp: (id, reason) =>
    req.post(`/allocation/allocations/${id}/give-up`, { reason }),
  releaseExpired: () => req.post('/allocation/allocations/release-expired'),
  waiting: (params) => req.get('/allocation/waiting', { params }),
  recalcWaiting: () => req.post('/allocation/waiting/recalc'),'''
    assert anchor in s, '锚点缺失'
    s = s.replace(anchor, add, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已补 setBatchStatus / giveUp / releaseExpired / waiting / recalcWaiting')
