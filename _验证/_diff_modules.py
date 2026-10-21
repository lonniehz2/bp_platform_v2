# -*- coding: utf-8 -*-
"""对比 console.html 的功能页签 与 新 SPA 的菜单页面"""
import io
import os
import re

CONSOLE = r'D:\Work\业务平台开发\backend\src\main\resources\static\console.html'
ROUTER = r'D:\Work\业务平台开发\frontend\src\router\index.js'

c = io.open(CONSOLE, encoding='utf-8').read()
# console 的页签：找 data-tab="xxx" 与其按钮文本
tabs = re.findall(r'<button[^>]*data-tab="([^"]+)"[^>]*>([^<]{1,30})</button>', c)
if not tabs:
    tabs = re.findall(r'data-tab="([^"]+)"[^>]*>\s*([^<\n]{1,30})', c)
print('console 页签 %d 个：' % len(tabs))
for k, v in tabs:
    print('  %-18s %s' % (k, v.strip()))

r = io.open(ROUTER, encoding='utf-8').read()
pages = re.findall(r"path: '/([a-z\-]+)',\s*\n\s*name: '[^']+',\s*\n\s*component: \(\) => import\('@/views/(\w+)\.vue'\),\s*\n\s*meta: \{ title: '([^']+)'", r)
print('\nSPA 菜单页面 %d 个：' % len(pages))
for path, comp, title in pages:
    print('  %-18s %-16s %s' % (path, comp, title))
