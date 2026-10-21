# -*- coding: utf-8 -*-
"""正确替换空间层级的验证路径"""
import io
import json

ORG = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json',
                    encoding='utf-8'))['orgId']
P = r'D:\Work\业务平台开发\_verify_all_pages.py'
import os
if not os.path.exists(P):
    P = r'D:\Work\业务平台开发\_验证\_verify_all_pages.py'

s = io.open(P, encoding='utf-8').read()
old = "'/api/v1/spaces?pageNum=1&pageSize=20'"
new = "'/api/v1/spaces/tree?orgId=%s'" % ORG
if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已替换为 %s' % new)
else:
    print('仍未见旧路径')
