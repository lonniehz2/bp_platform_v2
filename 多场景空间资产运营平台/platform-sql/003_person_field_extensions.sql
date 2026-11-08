-- 人员字段扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table bp_person add column gender varchar(10) null;
alter table bp_person add column birth_date date null;
alter table bp_person add column address varchar(255) null;
alter table bp_person add column employer varchar(128) null;
alter table bp_person add column emergency_contact varchar(128) null;
alter table bp_person add column remark varchar(500) null;
