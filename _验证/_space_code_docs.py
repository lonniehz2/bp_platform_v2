# -*- coding: utf-8 -*-
"""帮助与手册：空间编码按上级前缀预填 + 重复校验。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 帮助 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
OLD = """          '新增时「所属组织」选组织名、「上级节点」选空间树节点，都不再需要填 ID。',"""
NEW = """          '新增时「所属组织」选组织名、「上级节点」选空间树节点，都不再需要填 ID。',
          '「空间编码」会按上级编码自动预填前缀（如上级 DEMO-B1-U1 → 预填 DEMO-B1-U1-），只需补本级编码（如 01）；切换上级时前缀自动更新且保留已填后缀。',
          '编码重复会当场提示（如「编码已存在：DEMO-B1（A栋）」），保存前即被拦下；顶级空间的前缀取所属组织编码。',"""
n = 0
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    n += 1
s = re.sub(r"HELP_VERSION\s*=\s*'[^']*'", "HELP_VERSION = 'v1.4（2026-10-26）'", s, count=1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助更新:', n, '→ v1.4')

# ---------- 手册附录 Y ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 Y' not in t:
    t = t.rstrip() + '''

---

## 附录 Y　空间编码按上级前缀预填

### Y.1 规则

| 场景 | 预填内容 |
|---|---|
| 在上级节点下新增 | `上级空间编码 + "-"`（如上级 `DEMO-B1-U1` → `DEMO-B1-U1-`） |
| 新增顶级节点 | `所属组织编码 + "-"` |
| 切换上级节点 | 前缀自动替换，**用户已填的后缀保留** |
| 清空上级 | 回退到组织编码前缀 |

界面在编码框下方直接提示「已按上级编码预填前缀 X，只需在后面补本级编码（如 01）」。

### Y.2 重复提示

- 失焦即校验：在已加载的空间树中查找同编码，命中则表单标红并提示
  `编码已存在：DEMO-B1（A栋）`
- 点保存时再次校验，重复则阻止提交并弹出同样提示
- 后端仍保留最终校验（`空间编码已存在: xxx`），防止并发/跨组织漏判

### Y.3 实测

```
选中节点：1单元（DEMO-B1-U1）
弹窗预填：DEMO-B1-U1-
提示：已按上级编码预填前缀 DEMO-B1-U1-，只需在后面补本级编码（如 01）

输入已存在编码 DEMO-B1 → 提示：编码已存在：DEMO-B1（A栋）
```
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 Y')
