-- 智慧物业 V1 临时停车
create table if not exists prop_temp_parking (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  plate_no varchar(32) not null,
  parking_space_id bigint null,
  entry_time datetime not null,
  exit_time datetime null,
  hours decimal(10,2) null,
  hourly_rate decimal(14,2) null,
  amount decimal(14,2) null,
  bill_id bigint null,
  pay_method varchar(32) null,
  status varchar(20) not null default 'IN',
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_temp_project (tenant_id, project_id, status),
  key idx_prop_temp_plate (plate_no)
) engine=InnoDB default charset=utf8mb4 comment='临时停车记录';

insert ignore into prop_fee_item
(id, tenant_id, project_id, fee_item_code, fee_item_name, income_category, income_subcategory,
 charge_basis, billing_cycle, unit, default_price, status, is_deleted)
values
(377200000000000007, '350600', 370988445033697280, 'TEMP_PARKING', '临时停车费', 'PARKING',
 'TEMP_PARKING', 'FIXED', 'ONCE', '元', 0, 'ENABLED', 0);

insert ignore into prop_parking_rate
(id, tenant_id, project_id, garage_name, space_type, fee_type, billing_cycle, price,
 effective_from, status, is_deleted)
values
(377300000000000104, '350600', 370988445033697280, '临时停车', 'TEMP', 'TEMP', 'HOUR', 5.00,
 '2026-01-01', 'ENABLED', 0);
