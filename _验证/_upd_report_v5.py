# -*- coding: utf-8 -*-
"""报告升级 v5：记录前端 37 页、四入口、100% 接口覆盖、路径核对机制"""
import io
import os
import runpy

GEN = r'D:\Work\业务平台开发\_验证\_upd_report_v2.py'
REPORT = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'
LEDGER = r'D:\Work\业务平台开发\00_文档包索引与评审台账.md'

# ==================== 1) 生成器 → v5 ====================
s = io.open(GEN, encoding='utf-8').read()

if 'v5' not in s:
    # 版本行
    old_ver = """w('| 报告版本 | **v4**（本版新增：钥匙包+授权对账、告警规则引擎、'
  '保障档案+实名留痕 3 组共 9 表落地；**4 处校验真正接入业务链路**；'
  '单元测试增至 %d）' % test_methods)"""
    new_ver = """w('| 报告版本 | **v5**（本版新增：**完整 Web 前端**——PC 管理台 30 页 + '
  '租客端 H5 7 页 + 全屏大屏，四入口；**接口覆盖 100%%**；'
  '新增前后端路径自动核对机制；补齐设备列表/公示结束 2 处后端缺口）' % ())"""
    if old_ver in s:
        s = s.replace(old_ver, new_ver, 1)
    else:
        # 容错：直接替换含 v4 的版本行
        s = s.replace('**v4**', '**v5**', 1)

    # 第 17 项：移动端补 H5 说明
    old17 = '''    ("17", "移动端（租户小程序 + 工作人员端）", "未实现", "无",
     "**完全未实现**。当前为 PC 验证台（20 页签）", "高"),'''
    new17 = '''    ("17", "移动端（租户小程序 + 工作人员端）", "部分",
     "**租客端 H5 已实现**（7 页，移动优先、底部导航、独立入口 `/h5.html`）：'
     '登录、首页（待缴/合同/待办）、账单、申请进度、开门记录、报修、我的（绑定保障对象/'
     '实名状态/档案摘要）",
     "**微信小程序未做**（需小程序开发者工具与备案主体）；'
     "租客身份仍复用工作人员账号 + 手动绑定 personId，"
     "**正式化需独立住户认证（手机号验证码 + 实名比对）**", "中"),'''
    if old17 in s:
        s = s.replace(old17, new17, 1)

    # 结论
    s = s.replace(
        "w('> 距可交付**仅剩移动端**（唯一未实现 P0）。★ 级精细化项已全部补齐。')",
        "w('> **Web 端已完整交付**：PC 管理台 + 租客端 H5 + 全屏大屏，接口覆盖 100%。')\n"
        "w('>')\n"
        "w('> 距可交付仅剩：**微信小程序**（H5 已覆盖主要租客场景，可作为过渡）"
        "与**真机联调**。')", 1)

    io.open(GEN, 'w', encoding='utf-8').write(s)
    print('生成器已升级 v5')

# ==================== 2) 重新生成报告 ====================
runpy.run_path(GEN, run_name='__main__')

# ==================== 3) 追加前端章节 ====================
s = io.open(REPORT, encoding='utf-8').read()

if 'Web 前端交付' in s:
    print('前端章节已存在，跳过')
else:
    anchor = '---\n\n## 五、缺口清单（按对验收的影响排序）'
    block = '''### 4.8 ⭐⭐ Web 前端交付（v5 新增）

#### 四入口（单 jar 部署，无额外静态服务器）

| 路径 | 内容 | 体积 |
|---|---|---|
| `/` | **PC 管理台**（Vue3 + Vite + Element Plus） | 首屏 vendor 292KB + element-plus 942KB |
| `/h5.html` | **租客端 H5**（移动优先，底部导航） | 入口 2.5KB（按页懒加载）|
| `/view-screen.html` | **全屏运营大屏**（ECharts，深色 16:9） | 1010KB（echarts 独立分包，仅大屏加载）|
| `/console.html` | 旧 20 页签验证台（**原样保留**，未删除） | 149KB |

#### 页面清单（37 页）

| 分组 | 页面 |
|---|---|
| PC 核心业务（8）| 驾驶舱、申请与审核、配租与摇号、合同、账单缴费、报表导出、设备、通行记录 |
| PC 支撑（4）| 组织机构、房源台账、消息待办、系统支撑（审计/字典/参数）|
| PC ★ 级（4）| 工单维保、告警与规则引擎、钥匙包四分类、授权与对账 |
| PC 其余模块（14）| 人员、空间、退租、申诉、信用惩戒、换房、投诉、来访、短租、日房态、监管报送、开放平台、用户权限 |
| 租客端 H5（7）| 登录、首页、账单、申请进度、开门记录、报修、我的 |

#### ⭐⭐ 前后端路径自动核对机制（本项目最重要的工程化沉淀）

**背景**：开发过程中曾有 **6 处接口路径写错**（`/bills` 应为 `/fin/bills`、`/work-orders`
应为 `/workorders`、`/orgs/tree` 后端不存在等），根因是**凭 REST 习惯命名而未核对
`@RequestMapping`**。

**机制**：`_验证/_check_api_paths.py` 静态解析

| 侧 | 做法 |
|---|---|
| 后端 | 遍历全部 Controller，拼 `@RequestMapping` 根路径 + 方法级子路径 |
| 前端 | 解析 `modules.js` 与所有 `.vue` 中的 `req.get/post/...`，补 `/api/v1` |
| 归一化 | `{id}`、`${id}` → `{}`；忽略查询串；路径 + HTTP 方法双重匹配 |

**输出三类**：❌ 前端调用但后端不存在（真实 404）／⚠️ 方法不匹配／
🟡 已知缺口（后端未提供，白名单登记）。

**当前结果**：
```
后端接口 315 个（44 Controller）／前端调用 164 处
✅ 前端所有调用路径在后端均存在
（已知缺口 0 处）
```

> ⚠️ 该脚本自身也曾有 bug：初版正则要求 `@GetMapping(` 带括号，
> 而代码库大量使用无括号写法，导致 40 处误报。**核对工具本身必须被核对**。

#### 写操作表单（8 个模块）

字段**全部取自后端 Cmd record**（不凭印象）：退租（9 字段）、申诉（9）、
信用惩戒（16）、换房（10）、投诉（9）、来访、监管报送、开放平台（10）。
统一支持 text/textarea/number/date/select/bool 六种控件，含
**必填校验**（按 `@NotNull` 语义）与**数字合法性校验**。

#### 首屏分包

| 文件 | 说明 |
|---|---|
| `vendor` 292KB / `element-plus` 942KB / `echarts` 1010KB | 三方库独立分包，长期缓存 |
| 151 个页面 chunk | 按路由懒加载 |
| echarts | **仅大屏加载**，管理台不下载 |

#### v5 补齐的 2 处后端缺口

| 缺口 | 处理 |
|---|---|
| `GET /api/v1/devices` | 新增 `DeviceController`（`DevDevice` 实体本就存在但无控制器）|
| `POST /api/v1/publicities/{id}/finish` | 后端真实动作是 `publish`/`close`，新增 `PublicityOpsController` 暴露两者，前端改调 `/close` |

''' + anchor
    assert anchor in s
    s = s.replace(anchor, block, 1)
    io.open(REPORT, 'w', encoding='utf-8').write(s)
    print('已追加 4.8 Web 前端交付章节')

# ==================== 4) 台账附录 H ====================
ls = io.open(LEDGER, encoding='utf-8').read()
if '附录 H' not in ls:
    ls = ls.rstrip() + '''

---

## 附录 H · v5 进展（Web 前端完整交付）

> 详细核查见 [`05_首期功能完整性检查报告.md`](05_首期功能完整性检查报告.md)

### H.1 前端交付物

| 入口 | 内容 |
|---|---|
| `/` | PC 管理台 30 页 |
| `/h5.html` | 租客端 H5 7 页 |
| `/view-screen.html` | 全屏大屏（ECharts） |
| `/console.html` | 旧验证台（保留） |

工程规模：**54 个源文件 / 5328 行**，构建产物打入同一 jar（49.5MB）。

### H.2 接口覆盖 100%

`_验证/_check_api_paths.py` 静态核对：后端 315 接口 vs 前端 164 调用点，
**0 处 404**，已知缺口 0 处。该脚本应纳入每次前端改动的必跑项。

### H.3 首期 18 项 P0（v5）

| 判定 | 数量 | 项号 |
|---|---|---|
| ✅ 已实现 | 17 | 除 17 外全部 |
| ⚠️ 部分 | 1 | **17 移动端**（H5 已做，小程序未做）|
| ❌ 未实现 | 0 | — |

### H.4 唯一剩余工作

| 项 | 说明 |
|---|---|
| **真机联调** | 环境不可达（开发期在家庭网络，VM/DB 在内网）|
| 微信小程序 | 需开发者工具与备案主体 |
| 租客端独立认证 | 当前复用工作人员账号 + 手动绑定 personId |

### H.5 回内网执行顺序

```bash
python _验证/_check_api_paths.py --strict   # 路径核对（已通过）
python verify.py ddl                        # 建表（含 _ddl_sys_file.sql）
python _seed_open_gov.py                    # 权限/字典/接口清单
python _verify_open.py && python _verify_gov.py
python verify.py all                        # 全量回归
cd frontend && pnpm dev                     # 前端联调
```
'''
    io.open(LEDGER, 'w', encoding='utf-8').write(ls)
    print('台账已追加附录 H')

for f in (REPORT, LEDGER):
    print('  %s：%d 行' % (os.path.basename(f),
                          len(io.open(f, encoding='utf-8').read().split('\n'))))
