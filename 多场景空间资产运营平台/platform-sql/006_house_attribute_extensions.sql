-- 房源属性扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table bp_house add column layout_type varchar(32) null;
alter table bp_house add column orientation varchar(20) null;
alter table bp_house add column floor_no int null;
alter table bp_house add column total_floors int null;
