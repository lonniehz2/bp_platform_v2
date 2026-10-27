# -*- coding: utf-8 -*-
"""附录 AY：设备告警级别与详情显示。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()
if '附录 AY' not in s:
    s = s.rstrip() + '''

---

## 附录 AY　设备告警的级别与详情显示

### AY.1 问题

- 设备管理 →「设备告警」弹窗里，**级别**直接显示 `CRITICAL / WARN` 英文；
- **详情**直接显示原始 JSON，如 `{"pwdId":"1001"}`。

### AY.2 修复

| 位置 | 处理 |
|---|---|
| 后端 `EnumLabels` | 补 `WARN → 警告`（原只有 `WARNING`），`eventLevelLabel` 不再为空 |
| 新增 `utils/eventDisplay.js` | 级别中文映射 + 标签颜色；body 支持 JSON 字符串/对象/普通文本，按「中文键：值」展示，嵌套数组用顿号连接 |
| 设备管理告警弹窗 | 级别用 `levelLabel/levelTagType`，详情用 `fmtEventBody` |

### AY.3 实测（2026-10-28）

```
胁迫告警 → 级别「严重」；详情「密码/卡号：1001」
离线     → 级别「警告」；详情「原因：心跳超时 180 秒」
离线     → 级别「警告」；详情「原因：心跳超时 180 秒」
```

### AY.4 说明

- 设备事件页（DevEvents）原本已有格式化函数，本次抽到公共 utils，后续两处口径一致；
- 未知字段保留英文键名但值仍可读，不会整段吐 JSON。
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('附录 AY 已加')
