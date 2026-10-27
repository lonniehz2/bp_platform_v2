# -*- coding: utf-8 -*-
"""附录 AW：设备批量绑定三步 + 解绑修复。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()
if '附录 AW' not in s:
    s = s.rstrip() + '''

---

## 附录 AW　设备批量绑定与解绑修复

### AW.1 批量绑定（三步）

| 步骤 | 内容 |
|---|---|
| 1 选择文件 | CSV 列：房源编号, 设备编号（首行可为表头）；提供模板下载 |
| 2 校验预览 | 前端校验空值、文件内设备重复、房源+设备重复；预览全部行 |
| 3 绑定结果 | 调 `POST /devices/bind-batch` 逐行绑定，返回成功/失败与原因；失败行可导出 |

后端接口逐行处理：按房源编号找房源 → 取其空间 → 按设备编号找设备 →
设备已绑其它空间则失败并提示；单行失败不影响其它行。

### AW.2 顺带修复：解绑不生效

`POST /devices/{id}/bind` 传 `spaceId: null` 时，MyBatis-Plus 默认忽略 null 字段，
导致“解绑成功但空间仍在”。已改为 `LambdaUpdateWrapper.set(spaceId, null)` 显式置空。

### AW.3 实测（2026-10-27）

```
解绑：200，spaceId 变为 null
批量绑定 2 行：
  第1行 H8063501 + TEST-UNIT-3915694 → 成功（已绑定到空间 370832750846021632）
  第2行 H8063501 + NOT-EXIST-1       → 失败（设备 NOT-EXIST-1 不存在）
界面：三步步骤条「选择文件 / 校验预览 / 绑定结果」
```

### AW.4 说明

- 批量绑定只做“设备→空间”，房源通过空间定位，与单条绑定规则一致；
- 已绑定其它空间的设备不会自动搬家，需先解绑（安全考虑）。
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('附录 AW 已加')
