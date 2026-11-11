# 备份恢复演练记录

- 日期：2026-11-12
- 数据库：bp_platform_v2
- 方式：mysqldump --single-transaction --routines --triggers --events

## 结果

```text
备份文件：/tmp/bp_drill.sql.gz（约 346 KB）
恢复库：bp_restore_drill
```

关键表计数对比：

```text
bp_menu:            177 / 177
bp_org:             129 / 129
guarantee_contract: 755 / 755
```

格式：

```text
生产库 / 恢复库
```

## 结论

备份和恢复链路可用，恢复库数据量与生产库一致。

## 注意

本次是在本地 Docker MySQL 上演练，未覆盖：

```text
生产磁盘容量
生产备份耗时
生产网络传输
生产 MySQL 权限
```
