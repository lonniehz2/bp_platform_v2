# -*- coding: utf-8 -*-
"""在报告与台账中登记「验证脚本会清表」的作业顺序（避免再次掉进同一坑）"""

WARN = '''
---

## 附录 · ⚠️ 作业顺序陷阱（务必遵守）

`verify.py all` / `verify.py data` 的**数据初始化步骤会清空业务表并重建演示数据**，
但它**不包含以下前置数据**，跑完必须重新播种，否则登录会报「登录名或密码错误」：

| 顺序 | 命令 | 补齐内容 |
|---|---|---|
| 1 | `python verify.py all` | 清表 + 重建演示业务数据 |
| 2 | `python _seed_rbac.py` | **用户 3 / 角色 5 / 权限 12**（不补则无法登录）|
| 3 | `python _seed_open_gov.py` | `open:*` `gov:*` 权限 7 条 + 授权 13 条 + 字典 45 项 + 接口清单 8 个 |
| 4 | `python _seed_sys.py` | 政策参数 12 条、系统字典 |
| 5 | `python _seed_msg.py` | 消息模板 6 条 |

**实际案例**：v5 收尾时先跑完 `_verify_open.py`（40/40）与 `_verify_gov.py`（36/36），
再跑 `verify.py all`，结果 `bp_iam_user` 被清空，浏览器登录全部失败。
教训：**验证脚本会破坏它自己依赖的前置数据，播种必须在验证之后。**

建议把 2~5 步写成一个 `_seed_all.py` 一次执行，降低遗漏风险。
'''

for p in (r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md',
          r'D:\Work\业务平台开发\00_文档包索引与评审台账.md'):
    s = open(p, encoding='utf-8').read()
    if '作业顺序陷阱' in s:
        print('  - %s 已含该章节' % p.split('\\')[-1])
        continue
    open(p, 'a', encoding='utf-8').write(WARN)
    print('  ✓ %s 已追加「作业顺序陷阱」' % p.split('\\')[-1])
