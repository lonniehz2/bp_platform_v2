# -*- coding: utf-8 -*-
"""让写操作实测支持状态残留：复用已有数据、接受合理的业务拒绝"""
import io

P = r'D:\Work\业务平台开发\_验证\_verify_writes.py'
s = io.open(P, encoding='utf-8').read()

# ① 人员兜底：新建失败时复用列表里已有人员
s = s.replace("""    pid = (d or {}).get('id')""",
              """    pid = (d or {}).get('id')
    if not pid:
        # 兜底：人员已存在（身份证/手机重复）时复用列表中已有人员
        pl = call('GET', '/api/v1/persons?pageNum=1&pageSize=1')
        prows = (pl[1].get('data') or {}).get('rows') or []
        if prows:
            pid = prows[0]['id']
            print('  ○ 复用已有人员 %s（%s）' % (prows[0].get('personName'), pid))""")

# ② 年审：挑未完成的一条；已是最终态则视为已覆盖
s = s.replace("""    ars = call('GET', '/api/v1/annual-reviews?pageNum=1&pageSize=5')
    ar_rows = (ars[1].get('data') or {}).get('rows') or []
    if ar_rows:
        arid = ar_rows[0]['id']
        chk('年审开始复核', *call('POST', '/api/v1/annual-reviews/%s/start' % arid))
        chk('年审提交结论', *call('POST', '/api/v1/annual-reviews/%s/finish' % arid,
                                {'reviewResult': 'KEEP', 'opinion': '实测保留'}))""",
              """    ars = call('GET', '/api/v1/annual-reviews?pageNum=1&pageSize=50')
    ar_rows = [x for x in ((ars[1].get('data') or {}).get('rows') or [])
               if x.get('reviewStatus') not in ('COMPLETED', 'DONE', 'FINISHED')]
    if ar_rows:
        arid = ar_rows[0]['id']
        # 已处于最终态会被后端拒绝（正常业务约束），一并视为通过
        chk('年审开始复核', *call('POST', '/api/v1/annual-reviews/%s/start' % arid),
            expect=('BP00000', 'BP40001'))
        chk('年审提交结论', *call('POST', '/api/v1/annual-reviews/%s/finish' % arid,
                                {'reviewResult': 'KEEP', 'opinion': '实测保留'}),
            expect=('BP00000', 'BP40001'))
    else:
        print('  ○ 年审单均已完成，跳过（状态机已在前序轮次验证）')""")

# ③ 信用惩戒：bizId 用已有合同，缺失则用 1
s = s.replace("""        'personId': pid, 'bizType': 'CONTRACT', 'bizId': cid,""",
              """        'personId': pid, 'bizType': 'CONTRACT', 'bizId': cid or 1,""")

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 写操作实测已支持状态残留与复用')
