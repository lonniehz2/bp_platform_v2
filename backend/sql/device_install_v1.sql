-- 设备安装/虚拟设备与房源编号序号（2026-11-05）
-- 在既有库执行；install_time 已存在时跳过该列。

alter table bp_dev_device add column is_virtual tinyint not null default 0 comment '是否虚拟设备';
alter table bp_dev_device add column install_status varchar(32) not null default 'INSTALLED'
  comment 'VIRTUAL/PENDING_INSTALL/INSTALLED/PENDING_REPLACE/REPLACED';
alter table bp_dev_device add column iot_order_no varchar(64) null comment 'IoT安装单号';
alter table bp_dev_device add column mac_updated_time datetime null comment 'MAC更新时间';

create table if not exists bp_dev_device_hardware (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  device_id varchar(64) not null,
  old_mac varchar(64) null,
  new_mac varchar(64) null,
  change_type varchar(20) not null,
  iot_order_no varchar(64) null,
  operator_id varchar(64) null,
  operator_name varchar(100) null,
  install_time datetime null,
  remark varchar(500) null,
  create_time datetime not null default current_timestamp,
  key idx_hw_device (device_id),
  key idx_hw_order (iot_order_no)
) engine=InnoDB default charset=utf8mb4 comment='设备硬件/MAC更换历史';

create table if not exists bp_asset_house_seq (
  tenant_id varchar(32) not null,
  org_code varchar(32) not null,
  next_val bigint not null default 1,
  primary key (tenant_id, org_code)
) engine=InnoDB default charset=utf8mb4 comment='房源编号序号';

-- 清理重复房源后再加唯一约束：
-- alter table bp_asset_house add unique key uk_tenant_space (tenant_id, space_id, is_deleted);

-- 一空间一房源：逻辑删除时只约束有效房源
alter table bp_asset_house
  add column active_space_id bigint generated always as (if(is_deleted = 0, space_id, null)) stored;
alter table bp_asset_house
  add unique key uk_tenant_active_space (tenant_id, active_space_id);

create table if not exists bp_grant_freeze (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  house_id bigint not null,
  person_id bigint null,
  grant_id bigint null,
  keyring_id bigint null,
  freeze_scope varchar(20) not null default 'HOUSE',
  reason varchar(500) not null,
  freeze_status varchar(20) not null default 'FROZEN',
  original_status varchar(20) null,
  iot_order_no varchar(64) null,
  operator_id varchar(64) null,
  operator_name varchar(100) null,
  freeze_time datetime null,
  restore_time datetime null,
  error_msg varchar(500) null,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_freeze_house (house_id, freeze_status),
  key idx_freeze_person (person_id, freeze_status),
  key idx_freeze_grant (grant_id)
) engine=InnoDB default charset=utf8mb4 comment='授权冻结记录';
