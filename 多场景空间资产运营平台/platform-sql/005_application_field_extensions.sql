-- 保障申请档案字段扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table guarantee_application add column contact_phone varchar(32) null;
alter table guarantee_application add column income_level varchar(32) null;
alter table guarantee_application add column housing_status varchar(32) null;
alter table guarantee_application add column urgency varchar(20) null;
alter table guarantee_application add column remark varchar(500) null;
