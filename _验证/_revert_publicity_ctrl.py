# -*- coding: utf-8 -*-
"""撤回 PublicityOpsController（与原控制器路径冲突），前端改调既有 /close"""
import io
import os

# 1) 删除冲突控制器
p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\biz\controller\PublicityOpsController.java')
if os.path.exists(p):
    os.remove(p)
    print('  ✓ 已删除 PublicityOpsController.java（路径与原控制器冲突）')

# 2) 前端：只保留 close（publish 若原控制器有则保留调用，否则也不影响）
FE = r'D:\Work\业务平台开发\frontend\src\api\modules.js'
s = io.open(FE, encoding='utf-8').read()
old = """  // 后端真实动作是 close（结束公示）/ publish（发布），无 finish
  publish: (id) => req.post(`/publicities/${id}/publish`),
  close: (id, remark) => req.post(`/publicities/${id}/close`, { remark }),
  finish: (id, remark) => req.post(`/publicities/${id}/close`, { remark })"""
new = """  // 公示状态流转由既有 PublicityReviewController 提供；后端无 finish，用 close
  close: (id, remark) => req.post(`/publicities/${id}/close`, { remark }),
  finish: (id, remark) => req.post(`/publicities/${id}/close`, { remark })"""
if old in s:
    s = s.replace(old, new, 1)
    io.open(FE, 'w', encoding='utf-8').write(s)
    print('  ✓ 前端 modules.js：移除 publish，保留 close/finish')
else:
    print('  - modules.js 已符合预期')
