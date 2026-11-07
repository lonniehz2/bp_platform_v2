-- 智慧物业 V1 项目配置
create table if not exists prop_project_config (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  org_id bigint not null,
  project_code varchar(64) not null,
  project_name varchar(128) not null,
  company_name varchar(128),
  contact_name varchar(64),
  contact_phone varchar(32),
  service_phone varchar(32),
  address varchar(500),
  receipt_header varchar(128),
  bank_account varchar(128),
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64),
  create_time datetime not null default current_timestamp,
  update_by varchar(64),
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_project_org (tenant_id, org_id),
  key idx_project_code (tenant_id, project_code)
) engine=InnoDB default charset=utf8mb4 comment='物业项目配置';

insert ignore into prop_project_config
(id, tenant_id, org_id, project_code, project_name, company_name, service_phone, receipt_header, status, is_deleted)
values
(377100000000000001, '350600', 370988445033697280, 'DEMO', '演示小区', '演示物业公司',
 '400-000-0000', '演示物业公司', 'ENABLED', 0);
