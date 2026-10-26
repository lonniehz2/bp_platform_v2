# -*- coding: utf-8 -*-
"""帮助与手册：催缴单一主线（欠费处置），通知记录只读。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()

OLD = """          '「催缴通知」用于查看已发出的短信/微信/电话/上门/书面记录，也可手工登记。',"""
NEW = """          '「催缴通知」只读：查看历史上发出的短信/微信/电话/上门/书面记录（本版起不再新增，统一走下一条）。',"""

n = 0
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助文案更新:', n)

# 手册附录 S 补充说明
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if 'S.1.1' not in t:
    OLD2 = """页面能力：

- 扫描建议：按逾期天数聚合欠费合同，标记「建议冻结」，一键生成处置"""
    NEW2 = """**单一主线**：本版起催缴统一在「欠费处置」执行；「催缴通知」历史记录只读（不再新增），
避免两套模型各记一套。

页面能力：

- 扫描建议：按逾期天数聚合欠费合同，标记「建议冻结」，一键生成处置"""
    if OLD2 in t:
        t = t.replace(OLD2, NEW2, 1)
        io.open(P2, 'w', encoding='utf-8', newline='').write(t)
        print('手册附录 S 已补单一主线说明')
