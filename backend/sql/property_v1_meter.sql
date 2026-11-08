-- 智慧物业 V1 水电表与抄表
create table if not exists prop_meter (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint not null,
  meter_type varchar(20) not null,
  meter_no varchar(64) not null,
  device_id varchar(64) null,
  multiplier decimal(10,3) not null default 1,
  unit_price decimal(14,4) not null,
  initial_reading decimal(14,2) not null default 0,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_meter_no (tenant_id, project_id, meter_no),
  key idx_prop_meter_house (house_id)
) engine=InnoDB default charset=utf8mb4 comment='物业水电表';

create table if not exists prop_meter_reading (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  meter_id bigint not null,
  period varchar(7) not null,
  prev_reading decimal(14,2) not null,
  current_reading decimal(14,2) not null,
  usage_amount decimal(14,2) not null,
  unit_price decimal(14,4) not null,
  amount decimal(14,2) not null,
  bill_id bigint null,
  read_date date not null,
  status varchar(20) not null default 'BILLED',
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  unique key uk_prop_meter_period (tenant_id, meter_id, period),
  key idx_prop_meter_reading_project (project_id, period)
) engine=InnoDB default charset=utf8mb4 comment='物业抄表记录';

insert ignore into prop_fee_item
(id, tenant_id, project_id, fee_item_code, fee_item_name, income_category, income_subcategory,
 charge_basis, billing_cycle, unit, default_price, status, is_deleted)
values
(377200000000000005, '350600', 370988445033697280, 'ELECTRICITY', '电费', 'ENERGY',
 'ENERGY_ELECTRICITY', 'METER', 'MONTH', '元/度', 0.60, 'ENABLED', 0);
