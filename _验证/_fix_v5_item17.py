# -*- coding: utf-8 -*-
"""修正生成器中第 17 项的引号错误（第 135-137 行）"""
import io

P = r'D:\Work\业务平台开发\_验证\_upd_report_v2.py'
lines = io.open(P, encoding='utf-8').read().split('\n')

# 定位并整体替换第 17 项的 4 行（索引从 0 开始：134..137）
start = None
for i, ln in enumerate(lines):
    if '租客端 H5 已实现' in ln:
        start = i
        break

assert start is not None, '未找到第 17 项'
# 覆盖 start..start+5（含微信小程序与正式化两段）
new_block = [
    '     "**租客端 H5 已实现**（7 页，移动优先、底部导航、独立入口 `/h5.html`）："',
    '     "登录、首页（待缴/合同/待办）、账单、申请进度、开门记录、报修、"',
    '     "我的（绑定保障对象/实名状态/档案摘要）",',
    '     "**微信小程序未做**（需小程序开发者工具与备案主体）；'
    '租客身份仍复用工作人员账号 + 手动绑定 personId，'
    '**正式化需独立住户认证（手机号验证码 + 实名比对）**", "中"),',
]
lines[start:start + 6] = new_block

io.open(P, 'w', encoding='utf-8').write('\n'.join(lines))
print('已修正第 17 项（%d 行 → %d 行）' % (6, len(new_block)))
