# -*- coding: utf-8 -*-
"""把构建校验加入 _check_all.py，并追加文档"""
import io

# ---------- 1) _check_all.py 增加前端构建校验 ----------
P = r'D:\Work\业务平台开发\_验证\_check_all.py'
s = io.open(P, encoding='utf-8').read()

if '_check_build.py' not in s:
    s = s.replace("""STEPS = [
    ('接口路径核对（前后端一致性）', '_check_api_paths.py', STRICT),""",
                  """STEPS = [
    ('前端构建与静态校验', '_check_build.py', STRICT),
    ('接口路径核对（前后端一致性）', '_check_api_paths.py', STRICT),""", 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ _check_all.py 加入「前端构建与静态校验」')
else:
    print('  - 已包含')

# ---------- 2) 文档追加 ----------
REPORT = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'
LEDGER = r'D:\Work\业务平台开发\00_文档包索引与评审台账.md'

BLOCK = '''
---

## 附录 · v9 前端构建校验（补上「构建通过但页面坏」的盲区）

### N.1 为什么需要这个脚本

空间层级页出现过一次典型故障：`loadOrgs()` 里调用了 `orgApi.children()`，
但 `import` 只写了 `spaceApi`。结果：

- Vue 编译**不报错**
- `pnpm build` **通过**
- 打开页面 → `ReferenceError: orgApi is not defined` → `onMounted` 中断 → **树永远是空的**

当时我只验证了接口（`/spaces/tree` 返回 90 个节点 ✅）就交付了，
用户看到的是空白页。**接口正确 ≠ 页面能显示。**

### N.2 脚本做三件事

| 检查 | 说明 |
|---|---|
| ① 未定义标识符 | 扫描每个 `.vue`：模板表达式里出现的标识符，是否都在 `<script setup>` 中被 import 或声明。命中即报（抓 `orgApi` 这类漏导入）|
| ② 路由 ↔ 视图 | 路由引用的 `.vue` 是否都存在 |
| ③ 构建产物 | 每个视图是否都打进了 bundle（本项目 outDir 指向 `backend/.../static`）|

### N.3 上线即抓到 20 个真实缺陷

第一次运行就报出：

```
✗ Alerts / Appeals / Cashflow / … 共 15 个页面：HINT 未定义
✗ GovReport / HouseCalendar / OpenApps / ShortRent / Visits：TAG 未定义
```

原因是早期批量生成页面时，模板写了 `:title="HINT"` 与 `v-if="TAG"`
（生成脚本的占位符残留），导致：

- **15 个页面的提示条标题是空白**（用户看不到业务前提说明）
- **5 个页面的业务标签永不显示**（如「对接房管局/公安」）

已全部改为真实文案、去掉无效条件。

### N.4 用法

```bash
cd 业务平台开发/_验证

python _check_build.py            # 只报告
python _check_build.py --strict   # 有问题返回非 0

python _check_all.py              # 一键：构建 → 接口路径 → 显示层 → 46 页对照
```

### N.5 误报控制（重要）

脚本本身也需要维护，否则会被当成噪音忽略。已处理的误报来源：

| 来源 | 处理 |
|---|---|
| Vue 模板内置 `$route` / `$router` / `$emit` | 加入白名单 |
| `defineProps({ columns: ... })` 的属性 | 括号配平解析 props 顶层键 |
| 表格作用域变量 `row` / `item` / `index` | 加入白名单 |
| 字符串字面量里的内容 | 先剥离引号内容再匹配 |

**当前结果：55 个组件，0 处误报，0 处漏报。**

### N.6 维护约定

| 场景 | 动作 |
|---|---|
| 新增页面 | 跑 `_check_build.py`，确认无未定义标识符 |
| 改了页面但页面空白 | **先跑这个脚本**，大概率是漏 import |
| 删改了公共组件 | 跑一次；未定义标识符会连带报出 |
| 交付前 | 必须 `pnpm build`，否则脚本第③项查的是旧产物 |

### N.7 仍然覆盖不到的

| 类型 | 说明 |
|---|---|
| 运行时数据错误 | 如接口字段名不匹配（脚本查语法，不查语义）|
| 布局/样式 | 侧边栏不滚动、图表 0 高度 |
| 交互逻辑 | 点树节点右侧不刷新（前端传参后端不接）|

**结论：这个脚本把「漏 import 型故障」从「靠用户发现」变成「提交前自动发现」，
但不替代人眼验收。**
'''

for p in (REPORT, LEDGER):
    t = io.open(p, encoding='utf-8').read()
    if 'v9 前端构建校验' in t:
        print('  - %s 已含' % p.split('\\')[-1])
        continue
    io.open(p, 'a', encoding='utf-8').write(
        BLOCK if p == REPORT else BLOCK.replace('## 附录 · v9', '## 附录 O · v9'))
    print('  ✓ %s 已追加' % p.split('\\')[-1])

for p in (REPORT, LEDGER):
    print('  %s：%d 行' % (p.split('\\')[-1],
                           len(io.open(p, encoding='utf-8').read().split('\n'))))
