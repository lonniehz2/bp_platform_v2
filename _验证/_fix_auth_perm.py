# -*- coding: utf-8 -*-
"""认证接口不得加权限注解：/auth/login、/auth/logout、/auth/me 必须对所有登录用户开放，
否则普通账号连自己的权限都取不到（表现为 403，整个前端拿不到菜单）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'iam', 'controller', 'AuthController.java')

s = io.open(P, encoding='utf-8').read()
n = len(re.findall(r'@(?:com\.yundao\.bp\.iam\.security\.)?RequirePerm\(', s))
s = re.sub(r'\n[ \t]*@(?:com\.yundao\.bp\.iam\.security\.)?RequirePerm\("[^"]+"\)', '', s)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('AuthController：移除 %d 条权限注解' % n)
