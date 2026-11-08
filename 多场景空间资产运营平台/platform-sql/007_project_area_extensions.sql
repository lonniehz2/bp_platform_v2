-- 项目面积产权字段扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table bp_org add column total_area decimal(12,2) null;
alter table bp_org add column land_area decimal(12,2) null;
alter table bp_org add column property_type varchar(32) null;
alter table bp_org add column build_year int null;
