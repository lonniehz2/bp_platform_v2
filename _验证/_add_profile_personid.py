# -*- coding: utf-8 -*-
"""保障档案分页补 personId 过滤（前端查询框已改为人员ID）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'person')

# 1) 接口
p = os.path.join(J, 'service', 'GuaranteeProfileService.java')
s = io.open(p, encoding='utf-8').read()
if 'Long personId' not in s:
    s = s.replace('String profileStatus, String keyword);',
                  'String profileStatus, String keyword, Long personId);', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('接口 ok')

# 2) 控制器
p = os.path.join(J, 'controller', 'GuaranteeProfileController.java')
s = io.open(p, encoding='utf-8').read()
if 'Long personId' not in s:
    s = s.replace('@RequestParam(required = false) String keyword) {',
                  '''@RequestParam(required = false) String keyword,
            @RequestParam(required = false) Long personId) {''', 1)
    s = s.replace('profileStatus, keyword));', 'profileStatus, keyword, personId));')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('控制器 ok')

# 3) 实现
p = os.path.join(J, 'service', 'impl', 'GuaranteeProfileServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'Long personId)' not in s:
    s = s.replace('String profileStatus, String keyword) {',
                  'String profileStatus, String keyword, Long personId) {', 1)
    s = s.replace('                        .orderByDesc(PersonGuaranteeProfile::getId);',
                  '''                        .eq(personId != null, PersonGuaranteeProfile::getPersonId, personId)
                        .orderByDesc(PersonGuaranteeProfile::getId);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('实现 ok')
