# -*- coding: utf-8 -*-
"""附录 BB：短租可用性 + 换房次数。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()
if '附录 BB' not in s:
    s = s.rstrip() + '''

---

## 附录 BB　短租可用性与换房次数

### BB.1 短租可用性

短租订单 →「按房源查」弹窗内新增「可用性」区：选入住/退房日期 → 「查可用性」，
调 `GET /house-calendar/{houseId}/availability`，展示：

```
房源：00004 可整段出租（3/3 天可售）
```

不可整段出租时显示警示色提示。

**实测**：houseId=373351946444214272，2026-10-28 → 10-31 → days=3、freeDays=3、available=true。

### BB.2 换房已换次数

换房页列表新增「已换次数」列（`ExchangeVO.exchangeTimes`），
配合原有的「换房次数受限」提示，可以直观看某租期是否已用完换房额度。

### BB.3 文件下载与空间子树

- 文件下载：`FileUploader` 已使用 `/api/v1/files/{id}/download`（上传组件内直接下载），无需新增页面。
- 空间子树：`SpaceSelect` 目前按组织整棵树平铺，满足业务选择；`/spaces/{id}/subtree`
  仅在大组织下才有性能收益，暂不接入。

### BB.4 结论

至此 AZ 附录列出的 P1/P2 缺口已全部补齐或确认无需页面；剩余只有
「空间子树选择器」这一项性能优化，可选。
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('附录 BB 已加')
