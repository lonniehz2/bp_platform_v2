# -*- coding: utf-8 -*-
"""向 05 报告追加附录 Q（合同驱动房源占用）"""
import io
import os

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                   '05_首期功能完整性检查报告.md')

APPENDIX = u'''

---

## 附录 Q：合同驱动房源占用（占用联动）

### Q.1 问题

合同走到「履约中」后，房源状态与占用流水**完全没动**：

- 房源仍停留在 `VACANT` / `PENDING_ALLOC`
- `bp_asset_space_occupancy` 表 **0 行**

后果是同一套房可以被反复配租出去——系统里没有任何地方记得「这套房有人住」。

### Q.2 设计

新增 `OccupancyService`（asset 模块），由合同状态变化驱动，**与合同变更同事务**：

| 合同动作 | 占用动作 | 房源动作 |
|---|---|---|
| 签约生效 | 新增 `ACTIVE` 占用（租期、承租人、来源合同） | `OCCUPIED`，入住人数 +1 |
| 续签 | 更新占用 `end_date` | 不变 |
| 终止 / 到期 / 作废 | 占用置 `FINISHED`，回填实际结束日 | 无其它在用占用时回到 `VACANT`，人数 -1 |

四条关键约定：

1. **状态不直接赋值**：用 `HouseStatus.nextOf` 在状态机图上求最短路径，
   可达才写（如 `空置→锁定→已配租→已入住`），不可达直接拒绝——避免把
   脏状态写进库。
2. **幂等键**：`(source_type='CONTRACT', source_id, status='ACTIVE')`。
   重复签约/重复终止不会产生重复占用。
3. **合租安全**：允许多条 `ACTIVE` 并行占用；只有「一条都不剩」才释放房源。
4. **容量闸门**：入住人数已达 `max_capacity` 时拒绝再占，报「房源已满员」。

### Q.3 代码位置

| 文件 | 作用 |
|---|---|
| `asset/entity/SpaceOccupancy.java` | 占用流水实体（此前只有表没有实体） |
| `asset/mapper/SpaceOccupancyMapper.java` | Mapper |
| `asset/service/OccupancyService.java` | 接口：occupy / release / extend |
| `asset/service/impl/OccupancyServiceImpl.java` | 状态机寻路 + 幂等 + 容量校验 |
| `biz/service/impl/ContractServiceImpl.java` | 在 sign / terminate / cancel / expireDue / renew 五个动作处调用 |

### Q.4 验证

| 验证项 | 结果 |
|---|---|
| 接口全链路（建合同 → 待签 → 签约中 → 签约 → 终止） | 签约后房源 `OCCUPIED`、人数 1、占用 `ACTIVE`；终止后房源 `VACANT`、人数 0、占用 `FINISHED`（结束日回填当天） |
| E2E 断言「签约后房源被占用」 | 通过，E2E 由 9 条增至 **10 条断言，10/10** |
| 历史数据修补 `_backfill_occupancy.py` | 为 11 份已履约但无占用的合同补建占用；复跑显示待补 0 份（幂等） |
| 房源状态分布 | `OCCUPIED` 3536 → 3547，`PENDING_ALLOC` 1104 → 1093 |

配套脚本：

```bash
python _diag_occupy_cycle.py        # 占房/退房全链路验证（自动清理）
python _backfill_occupancy.py --dry # 查看历史合同待补占用
python _backfill_occupancy.py       # 补建（幂等，可重复执行）
python _cleanup_e2e.py              # 清理时连带回滚占用与房源状态
```

**注意**：`_cleanup_e2e.py` 现在会先删占用、再删合同、最后把无在用占用的房源
放回空置。否则每跑一轮 E2E 都会留下一间「已入住但没有合同」的僵尸房源。
'''

with io.open(DOC, 'a', encoding='utf-8') as f:
    f.write(APPENDIX)
print('已追加附录 Q，总行数：%d' % len(io.open(DOC, encoding='utf-8').readlines()))
