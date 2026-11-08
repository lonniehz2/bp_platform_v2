-- 保障档案扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table guarantee_application add column guarantee_type varchar(32) null;
alter table guarantee_application add column family_type varchar(32) null;
alter table guarantee_application add column subsidy_status varchar(32) null;
alter table guarantee_application add column archive_no varchar(64) null;
