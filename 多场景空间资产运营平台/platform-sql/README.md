# platform-sql

> 新平台数据库草案目录  
> 数据库：`bp_platform_v2`  
> 当前状态：框架设计阶段，未执行

## 目录规划

```text
001_platform_core.sql       租户/场景/组织/权限
002_asset_model.sql         空间模板/资产类型/空间/房屋
003_person_model.sql        人员/关系/标签/组
004_workflow.sql            审批/工作流
005_contract_booking.sql    合同/预订/入住/库存
006_billing_discount.sql    计费/收款/发票/优惠
007_device_grant.sql        设备业务/授权
008_scene_guarantee.sql     保障房场景
009_scene_property.sql      物业场景
010_migration.sql           老库迁移
```

## 原则

```text
平台表 bp_*
保障房表 guarantee_*
物业表 prop_*
外部表 iot_*/parking_*
平台表不依赖场景表
```

## 迁移

```text
老库：bp_platform
新库：bp_platform_v2
迁移期间老库只读
新库写入
不做长期双写
```


## 老数据迁移

```powershell
$env:DB_PASSWORD='******'
python migrate_legacy.py          # dry-run
python migrate_legacy.py --apply  # 实际写入
```

报告：[05-老数据迁移报告](../platform-docs/05-老数据迁移报告.md)
