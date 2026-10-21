# -*- coding: utf-8 -*-
"""修正验证脚本：空间层级改用 /spaces/tree?orgId="""
import io
import json

ORG = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json',
                    encoding='utf-8'))['orgId']
P = r'D:\Work\业务平台开发\_验证\_verify_all_pages.py'
s = io.open(P, encoding='utf-8').read()

old = "('/api/v1/spaces?pageNum=1&pageSize=20', True)"
new = "('/api/v1/spaces/tree?orgId=%s', True)" % ORG
if old in s:
    s = s.replace(old, new.replace(' ', '').join(['', '']) if False else new, 1)
    # 保持元组结构：('空间层级', 'GET', '/api/v1/spaces/tree?orgId=xxx', True)
    s = s.replace("('空间层级', 'GET', '/api/v1/spaces/tree?orgId=%s', True),"
                  % ORG,
                  "('空间层级', 'GET', '/api/v1/spaces/tree?orgId=%s', True),"
                  % ORG)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已改为 /spaces/tree?orgId=%s' % ORG)
else:
    print('锚点未找到，当前空间行：')
    for ln in s.split('\n'):
        if '空间层级' in ln:
            print('  ' + ln.strip())
