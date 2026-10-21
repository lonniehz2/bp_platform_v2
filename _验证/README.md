# 数据库一键验证 · 使用说明

## 快速开始（明天到公司网络后）

```powershell
cd D:\Work\业务平台开发\_验证

# 1) 先确认能连上数据库
py verify.py check

# 2) 一键全流程（建表 → 回读校验 → 冒烟）
py verify.py all

# 3) 完整验证（含压测数据与性能，耗时较长约 10 分钟）
py verify.py full
```

> `py` 若不可用，用完整路径：
> `"C:\Program Files\DSH Desktop\resources\office-runtime\primary-runtime\dependencies\python\python.exe" verify.py all`

---

## 命令清单

| 命令 | 作用 | 耗时 |
|---|---|---|
| `check` | 连通性 + 版本 + 排序规则可用性 + 现有表数 | 5s |
| `ddl` | 执行 P1~P5 建表（重建库，**115 表**） | ~90s |
| `readback` | 结构回读 + **关键指标断言** | 10s |
| `smoke` | 埋读/唯一约束/分区路由 | 10s |
| `data` | 生成压测数据（5771 房源 / 1.5 万人 / 30 万通行记录） | ~8min |
| `perf` | 查询性能与执行计划 | ~2min |
| `all` | `check` + `ddl` + `readback` + `smoke` | ~2min |
| `full` | `all` + `data` + `perf` | ~10min |
| `clean` | 删除测试库（需输入库名确认） | 2s |

---

## 换数据库 / 换网络

**只改 `config.json`**，脚本无需改动：

```json
{
  "db": {
    "host": "192.168.31.153",
    "port": 33306,
    "user": "root",
    "password": "5677@Mysql",
    "database": "bp_platform"
  }
}
```

也可以多份配置并存：
```powershell
py verify.py check -c config_office.json
py verify.py all   -c config_office.json
```

> ⚠️ **家庭网 ↔ 公司网切换时最常见的问题就是 host 变了**。
> `verify.py check` 会在连不上时直接提示这一点。

---

## 断言项（readback 步骤）

| 项 | 期望值 | 来源 |
|---|---|---|
| 表数量 | **115** | `config.json` → `expect.tables` |
| 列数量 | **2036** | `expect.columns` |
| 列注释覆盖率 | **100%** | `expect.comment_coverage` |
| 缺主键表数 | 0 | 固定 |
| 分区表分区数 | 7 | `bp_dev_access_record` |

任一不符 → **退出码 1**，可直接用于 CI。

---

## 目录结构

```
_验证/
├── verify.py          # 一键入口（编排 + 断言 + 汇总）
├── common.py          # 公共模块（配置、连接、彩色输出、子进程执行）
├── config.json        # 数据库连接与期望值
├── README.md          # 本文件
└── steps/             # 各步骤脚本（连接参数已改为读环境变量）
    ├── _run_ddl.py            # 执行 P1~P5
    ├── _verify_db.py          # 结构回读
    ├── _smoke.py              # 冒烟测试
    ├── _gen_perf_data3.py     # 基础数据
    ├── _gen_access.py         # 通行记录
    ├── _perf_test2.py         # 查询性能
    ├── _perf_workorder.py     # 工单 SLA
    └── _bench_insert.py       # 写入方法基准
```

---

## 已验证的事实（供参考）

以下结论来自改动前在真实库上的执行记录：

| 项 | 结果 |
|---|---|
| 原 111 表 DDL 执行 | **118/118 语句成功，0 失败** |
| 结构回读 | 111 表 / 1906 列，与设计一致 |
| 分区路由 | 按月正确落分区，**`pmax` 兜底分区 0 行** |
| 幂等约束 | 重复 `event_id` 被拒（`ERROR 1062`） |
| 分区裁剪 | 单日查询仅命中 1 个分区；无时间条件扫全部 7 个 |
| 幂等查询访问类型 | `type=const`（最优） |

**待验证**：整合后 **115 表 / 2036 列** 的全量真机验证（本次因家庭网与测试库不同网段未能执行）。

---

## 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| `Can't connect ... (timed out)` | 网络不同网段 / host 变了 | 改 `config.json` 的 host |
| `Unknown collation: utf8mb4_0900_ai_ci` | MySQL 5.7 | 需 8.0+（`check` 会提前警告） |
| `readback FAIL 表数量` | DDL 未完整执行 | 看 `ddl` 步骤日志 |
| 灌数很慢（<500 行/秒） | 用了 `executemany` 语义 | 已改为多值 INSERT；另注意 `sync_binlog=1` 会限制吞吐 |
| 连接被服务器断开 | 测试机资源耗尽 | 减少 `data.access_records` 或分批执行 |
