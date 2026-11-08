-- 设备导入字段扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

alter table bp_dev_device add column device_mac varchar(64) null;
alter table bp_dev_device add column is_virtual tinyint not null default 0;
alter table bp_dev_device add column install_status varchar(20) not null default 'INSTALLED';
create index idx_dev_device_mac on bp_dev_device(tenant_id, device_mac);
