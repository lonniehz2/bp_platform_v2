-- 智慧物业 V1 车位与周期价
create table if not exists prop_parking_space (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  garage_name varchar(64) not null,
  space_no varchar(64) not null,
  space_type varchar(32) not null default 'STANDARD',
  area decimal(10,2) null,
  owner_person_id bigint null,
  status varchar(20) not null default 'ENABLED',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_parking_no (tenant_id, project_id, garage_name, space_no),
  key idx_prop_parking_project (project_id, status)
) engine=InnoDB default charset=utf8mb4 comment='物业车位';

create table if not exists prop_parking_rate (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  garage_name varchar(64) null,
  space_type varchar(32) not null default 'STANDARD',
  fee_type varchar(20) not null default 'MANAGEMENT',
  billing_cycle varchar(20) not null,
  price decimal(14,2) not null,
  effective_from date not null,
  effective_to date null,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_parking_rate (tenant_id, project_id, garage_name, space_type, fee_type, billing_cycle)
) engine=InnoDB default charset=utf8mb4 comment='车位周期价';

create table if not exists prop_parking_plan (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  parking_space_id bigint not null,
  owner_person_id bigint null,
  fee_type varchar(20) not null default 'MANAGEMENT',
  billing_cycle varchar(20) not null,
  unit_price decimal(14,2) not null,
  start_date date not null,
  end_date date not null,
  next_due_date date null,
  bill_id bigint null,
  auto_renew tinyint not null default 0,
  plan_status varchar(20) not null default 'ACTIVE',
  termination_date date null,
  refund_amount decimal(14,2) null,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_parking_plan_space (parking_space_id, plan_status),
  key idx_prop_parking_plan_project (project_id, next_due_date)
) engine=InnoDB default charset=utf8mb4 comment='车位计费方案';

insert ignore into prop_parking_space
(id, tenant_id, project_id, garage_name, space_no, space_type, area, status, is_deleted)
values
(377300000000000001, '350600', 370988445033697280, '地下车库', 'B1-001', 'STANDARD', 12.00, 'ENABLED', 0),
(377300000000000002, '350600', 370988445033697280, '地下车库', 'B1-002', 'STANDARD', 12.00, 'ENABLED', 0),
(377300000000000003, '350600', 370988445033697280, '地下车库', 'B1-003', 'STANDARD', 12.00, 'ENABLED', 0);

insert ignore into prop_parking_rate
(id, tenant_id, project_id, garage_name, space_type, fee_type, billing_cycle, price,
 effective_from, status, is_deleted)
values
(377300000000000101, '350600', 370988445033697280, '地下车库', 'STANDARD', 'MANAGEMENT', 'MONTH', 100.00, '2026-01-01', 'ENABLED', 0),
(377300000000000102, '350600', 370988445033697280, '地下车库', 'STANDARD', 'MANAGEMENT', 'YEAR', 960.00, '2026-01-01', 'ENABLED', 0),
(377300000000000103, '350600', 370988445033697280, '地下车库', 'STANDARD', 'RENT', 'MONTH', 300.00, '2026-01-01', 'ENABLED', 0);
