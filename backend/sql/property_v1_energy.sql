-- 智慧物业 V1 公共能耗分摊
create table if not exists prop_energy_allocation (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  period varchar(7) not null,
  house_id bigint not null,
  area decimal(14,2) not null,
  total_amount decimal(14,2) not null,
  total_area decimal(14,2) not null,
  amount decimal(14,2) not null,
  bill_id bigint null,
  status varchar(20) not null default 'BILLED',
  create_time datetime not null default current_timestamp,
  unique key uk_prop_energy_house_period (tenant_id, project_id, period, house_id),
  key idx_prop_energy_period (tenant_id, project_id, period)
) engine=InnoDB default charset=utf8mb4 comment='公共能耗按面积分摊';

insert ignore into prop_fee_item
(id, tenant_id, project_id, fee_item_code, fee_item_name, income_category, income_subcategory,
 charge_basis, billing_cycle, unit, default_price, status, is_deleted)
values
(377200000000000006, '350600', 370988445033697280, 'ENERGY_SHARED', '公摊能耗费', 'ENERGY',
 'ENERGY_SHARED', 'AREA', 'MONTH', '元', 0, 'ENABLED', 0);
