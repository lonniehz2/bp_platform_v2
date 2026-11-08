-- 智慧物业 V1 租赁合同收入
create table if not exists prop_lease_contract (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_no varchar(64) not null,
  asset_type varchar(32) not null,
  asset_name varchar(200) not null,
  lessee_name varchar(128) not null,
  lessee_phone varchar(32) null,
  start_date date not null,
  end_date date not null,
  rent_amount decimal(14,2) not null,
  billing_cycle varchar(20) not null default 'MONTH',
  next_bill_date date null,
  status varchar(20) not null default 'ACTIVE',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_lease_no (tenant_id, contract_no),
  key idx_prop_lease_project (tenant_id, project_id, status)
) engine=InnoDB default charset=utf8mb4 comment='物业租赁合同';

insert ignore into prop_fee_item
(id, tenant_id, project_id, fee_item_code, fee_item_name, income_category, income_subcategory,
 charge_basis, billing_cycle, unit, default_price, status, is_deleted)
values
(377200000000000008, '350600', 370988445033697280, 'LEASE_RENT', '租赁租金', 'LEASE',
 'LEASE_RENT', 'FIXED', 'MONTH', '元', 0, 'ENABLED', 0);
