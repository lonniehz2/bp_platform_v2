-- 智慧物业 V1 支出
create table if not exists prop_expense (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  expense_month date not null,
  category_code varchar(64) not null,
  subcategory_code varchar(64) null,
  amount decimal(14,2) not null,
  supplier varchar(128) null,
  invoice_no varchar(128) null,
  pay_method varchar(32) null,
  remark varchar(500) null,
  status varchar(20) not null default 'CONFIRMED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_expense_project (tenant_id, project_id, expense_month),
  key idx_prop_expense_category (category_code)
) engine=InnoDB default charset=utf8mb4 comment='物业支出';
