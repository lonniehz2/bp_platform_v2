# -*- coding: utf-8 -*-
"""修正年审复核接口路径 + 修正写操作实测脚本的测试数据"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 前端 api：review → start/finish ----------
A = os.path.join(FE, 'api', 'modules.js')
s = io.open(A, encoding='utf-8').read()

old = """  review: (id, data) => req.post(`/annual-reviews/${id}/review`, data)"""
new = """  // 后端真实动作：start 开始复核 → finish 提交结论（原 review 路径不存在）
  start: (id) => req.post(`/annual-reviews/${id}/start`),
  finish: (id, data) => req.post(`/annual-reviews/${id}/finish`, data),
  markOverdue: () => req.post('/annual-reviews/mark-overdue')"""
if old in s:
    s = s.replace(old, new, 1)
    io.open(A, 'w', encoding='utf-8').write(s)
    print('  ✓ modules.js：annualReviewApi.review → start/finish')
else:
    print('  - modules.js 未匹配，检查：')
    for ln in s.split('\n'):
        if 'annual-review' in ln.lower():
            print('    ' + ln.strip()[:100])

# ---------- 2) 页面：复核按钮改为 start + finish ----------
P = os.path.join(FE, 'views', 'AnnualReviews.vue')
p = io.open(P, encoding='utf-8').read()

if 'annualReviewApi.finish' not in p:
    p = p.replace("""    await annualReviewApi.review(current.value.id, { ...r })""",
                  """    await annualReviewApi.start(current.value.id)
    await annualReviewApi.finish(current.value.id, { ...r })""", 1)
    io.open(P, 'w', encoding='utf-8').write(p)
    print('  ✓ AnnualReviews.vue：复核改为 start → finish')

# ---------- 3) 写操作实测脚本：修正测试数据 ----------
W = r'D:\Work\业务平台开发\_验证\_verify_writes.py'
w = io.open(W, encoding='utf-8').read()

FIX = [
    # 空间：单元下必须是楼层
    ("""    d = chk('新建空间-房间', *call('POST', '/api/v1/spaces', {
        'orgId': new_org or ORG, 'parentId': uid, 'spaceCode': 'WTR' + sfx,
        'spaceName': '实测房间', 'spaceType': 'ROOM', 'area': 66, 'sortNo': 1}))
    rid = (d or {}).get('id')""",
     """    d = chk('新建空间-楼层', *call('POST', '/api/v1/spaces', {
        'orgId': new_org or ORG, 'parentId': uid, 'spaceCode': 'WTF' + sfx,
        'spaceName': '实测楼层', 'spaceType': 'FLOOR', 'sortNo': 1}))
    fid_space = (d or {}).get('id')
    d = chk('新建空间-房间', *call('POST', '/api/v1/spaces', {
        'orgId': new_org or ORG, 'parentId': fid_space, 'spaceCode': 'WTR' + sfx,
        'spaceName': '实测房间', 'spaceType': 'ROOM', 'area': 66, 'sortNo': 1}))
    rid = (d or {}).get('id')"""),
    # 手机号：11 位
    ("""        'phone': '13900139' + sfx, 'orgId': new_org or ORG,""",
     """        'phone': '139' + str(int(sfx) % 100000000).zfill(8), 'orgId': new_org or ORG,"""),
    # 投诉枚举
    ("""        'complaintType': 'SERVICE', 'source': 'PHONE', 'title': '实测投诉',""",
     """        'complaintType': 'COMPLAINT', 'source': 'PHONE', 'title': '实测投诉',"""),
    # 告警级别
    ("""        'alertCategory': 'SAFETY', 'alertType': 'TEST', 'alertLevel': 'WARNING',""",
     """        'alertCategory': 'SAFETY', 'alertType': 'SAFETY', 'alertLevel': 'NORMAL',"""),
    # 来访
    ("""    chk('新建来访', *call('POST', '/api/v1/visits', {
        'visitorName': '实来访', 'visitorPhone': '13900139001',
        'visitReason': '探亲', 'orgId': new_org or ORG, 'personId': pid}))""",
     """    chk('新建来访', *call('POST', '/api/v1/visits', {
        'visitType': 'ROUTINE', 'houseId': hid, 'personId': pid,
        'orgId': new_org or ORG, 'visitDate': '2026-10-21',
        'visitResult': '正常', 'visitorName': '实来访'}))"""),
    # 信用惩戒
    ("""        'personId': pid, 'bizType': 'RENT', 'bizId': 1,
        'violationType': 'ARREARS', 'violationDesc': '实测', 'sanctionType': 'BAN',
        'banYears': 1, 'decideOrgId': new_org or ORG, 'decideUserId': 1}))""",
     """        'personId': pid, 'bizType': 'CONTRACT', 'bizId': cid,
        'violationType': 'ARREARS', 'violationDesc': '实测',
        'sanctionType': 'BAN_APPLY', 'banYears': 1,
        'decideOrgId': new_org or ORG, 'decideUserId': 1}))"""),
    # 年审复核：改为 start → finish
    ("""    if ar_rows:
        chk('年审复核(保留)', *call(
            'POST', '/api/v1/annual-reviews/%s/review' % ar_rows[0]['id'],
            {'reviewResult': 'KEEP', 'opinion': '实测保留'}))""",
     """    if ar_rows:
        arid = ar_rows[0]['id']
        chk('年审开始复核', *call('POST', '/api/v1/annual-reviews/%s/start' % arid))
        chk('年审提交结论', *call('POST', '/api/v1/annual-reviews/%s/finish' % arid,
                                {'reviewResult': 'KEEP', 'opinion': '实测保留'}))"""),
]

n = 0
for old, new in FIX:
    if old in w:
        w = w.replace(old, new, 1)
        n += 1
io.open(W, 'w', encoding='utf-8').write(w)
print('  ✓ 实测脚本修正 %d 处测试数据' % n)
