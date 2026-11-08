-- 项目字段扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table bp_org add column address varchar(255) null;
alter table bp_org add column contact_name varchar(64) null;
alter table bp_org add column contact_phone varchar(32) null;
alter table bp_org add column remark varchar(500) null;
