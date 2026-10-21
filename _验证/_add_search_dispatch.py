# -*- coding: utf-8 -*-
"""人员检索三处改进：

1. /persons 关键字扩展：姓名 / 工号 / 手机 / 身份证号 都能搜
   （原来只搜姓名与人员编码，导致「按手机号搜不到」）
2. /applications 增加 personId 精确过滤
   （原来不认 personId，页面按人员筛选后结果毫无变化）
3. 前端 PersonPicker 按位数自动分流查询：
   19 位及以上 → 人员ID；18 位（含末位 X）→ 身份证号；11 位 → 手机号；其余 → 姓名
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(path, pairs, label):
    s = io.open(path, encoding='utf-8').read()
    n = 0
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b, 1)
            n += 1
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('%s：%d/%d' % (label, n, len(pairs)))


# 1) /persons 关键字支持手机与身份证
patch(os.path.join(J, 'person', 'service', 'impl', 'PersonServiceImpl.java'), [
    ('''            qw.and(w -> w.like(Person::getPersonName, keyword)
                    .or().like(Person::getPersonCode, keyword));''',
     '''            qw.and(w -> w.like(Person::getPersonName, keyword)
                    .or().like(Person::getPersonCode, keyword)
                    .or().like(Person::getPhone, keyword)
                    .or().like(Person::getIdCard, keyword));'''),
], '人员关键字扩展')

# 2) /applications 增加 personId
ac = os.path.join(J, 'biz', 'controller', 'ApplicationController.java')
s = io.open(ac, encoding='utf-8').read()
if 'personId' not in s:
    s = s.replace('@RequestParam(required = false) Long orgId,',
                  '''@RequestParam(required = false) Long orgId,
                                             @RequestParam(required = false) Long personId,''', 1)
    s = s.replace('service.page(pageNum, pageSize, securityType, status, orgId',
                  'service.page(pageNum, pageSize, securityType, status, orgId, personId')
    io.open(ac, 'w', encoding='utf-8', newline='').write(s)
    print('申请控制器：已加 personId')

# 服务接口与实现
sp = os.path.join(J, 'biz', 'service', 'ApplicationService.java')
s = io.open(sp, encoding='utf-8').read()
if 'personId' not in s:
    import re
    m = re.search(r'PageResult<ApplicationVO> page\(([^;]*)\);', s)
    if m:
        args = m.group(1)
        if 'personId' not in args:
            s = s[:m.start(1)] + args.rstrip() + ', Long personId' + s[m.end(1):]
            io.open(sp, 'w', encoding='utf-8', newline='').write(s)
            print('申请 service 接口：已加 personId')

ip = os.path.join(J, 'biz', 'service', 'impl', 'ApplicationServiceImpl.java')
s = io.open(ip, encoding='utf-8').read()
if 'long orgId' in s and 'personId)' not in s.split('public PageResult<ApplicationVO> page')[1][:300]:
    s = s.replace('''                                     Long orgId''', '''                                     Long orgId, Long personId''', 1)
    s = s.replace('''                        .eq(orgId != null, BizApplication::getOrgId, orgId)''',
                  '''                        .eq(orgId != null, BizApplication::getOrgId, orgId)
                        .eq(personId != null, BizApplication::getPersonId, personId)''', 1)
    io.open(ip, 'w', encoding='utf-8', newline='').write(s)
    print('申请实现：已加 personId 过滤')
