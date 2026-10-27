# -*- coding: utf-8 -*-
"""文档同步：常开常闭 + 上线清单。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 15 号：指令能力表补常开常闭
p = os.path.join(ROOT, '15_IoT对接接口与回调清单.md')
s = io.open(p, encoding='utf-8').read()
if 'LOCK_ALWAYS_OPEN' not in s:
    s = s.replace('| `METER_SWITCH` | 拉合闸 | `/ymd/restful/meter/switch` |',
                  '| `METER_SWITCH` | 拉合闸 | `/ymd/restful/meter/switch` |\n'
                  '| `LOCK_ALWAYS_OPEN` / `LOCK_ALWAYS_CLOSE` / `LOCK_MODE_NORMAL` | 常开/常闭/恢复 | `/ymd/restful/lock/mode`（`mode=OPEN/CLOSE/NORMAL`） |', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('15 指令能力已补常开常闭')

# 18 号：第 3 项改为「平台已定义契约，待 IoT 实现」
p = os.path.join(ROOT, '18_IoT平台需增加或完善的内容清单.md')
s = io.open(p, encoding='utf-8').read()
s = s.replace('常开/常闭能力与参数未定义', '常开/常闭：平台已支持（`LOCK_ALWAYS_OPEN/CLOSE/NORMAL` → `mode=OPEN/CLOSE/NORMAL`），待 IoT 实现 `/ymd/restful/lock/mode`')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('18 常开常闭状态已更新')

# 19 号：M4-07 阻塞 → 部分；数量调整
p = os.path.join(ROOT, '19_IoT联调测试执行报告.md')
s = io.open(p, encoding='utf-8').read()
s = s.replace('| TC-M4-07 | 常开/常闭 | ⛔ | 需 IoT 提供该能力与参数定义 |',
              '| TC-M4-07 | 常开/常闭 | 🟡 | 平台已支持 `LOCK_ALWAYS_OPEN/CLOSE/NORMAL`（映射 mode=OPEN/CLOSE/NORMAL），待 IoT 实现 `/ymd/restful/lock/mode` 后用真机验证 |')
s = s.replace('| ✅ 通过 | 平台侧行为已验证（mock/模拟） | 41 |',
              '| ✅ 通过 | 平台侧行为已验证（mock/模拟） | 41 |')
s = s.replace('| 🟡 部分 | 平台侧通过，设备侧行为待真实环境验证 | 11 |',
              '| 🟡 部分 | 平台侧通过，设备侧行为待真实环境验证 | 12 |')
s = s.replace('| ⛔ 阻塞 | 依赖 IoT 提供接口/参数/环境 | 5 |',
              '| ⛔ 阻塞 | 依赖 IoT 提供接口/参数/环境 | 4 |')
s = s.replace('| 3 | 常开/常闭能力与参数未定义 | TC-M4-07 |',
              '| 3 | 常开/常闭：平台已定义契约，待 IoT 实现 `/ymd/restful/lock/mode` | TC-M4-07 |')
s = s.replace('- **57 条用例：41 通过 / 11 部分 / 5 阻塞**，P0 无阻塞；',
              '- **57 条用例：41 通过 / 12 部分 / 4 阻塞**，P0 无阻塞；')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('19 用例状态与汇总已更新')

# 索引：加 20 号
p = os.path.join(ROOT, '00_文档包索引与评审台账.md')
s = io.open(p, encoding='utf-8').read()
if '20_IoT联调上线切换清单' not in s:
    m = re.search(r'^.*19_IoT联调测试执行报告\.md.*$', s, re.M)
    if m:
        line = m.group(0)
        s = s.replace(line, line + '\n| 20 | [20_IoT联调上线切换清单.md](20_IoT联调上线切换清单.md) | 切换开关、步骤、回滚、Go/No-Go | 上线 |', 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print('索引已补 20')
