-- 智慧物业 V1 电子发票申请
create table if not exists prop_invoice (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  receipt_id bigint not null,
  payment_id bigint null,
  invoice_no varchar(64) null,
  invoice_title varchar(200) not null,
  tax_no varchar(64) null,
  email varchar(128) null,
  amount decimal(14,2) not null,
  invoice_status varchar(20) not null default 'PENDING',
  invoice_url varchar(500) null,
  fail_reason varchar(500) null,
  requested_at datetime not null,
  issued_at datetime null,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_invoice_project (tenant_id, project_id, invoice_status),
  key idx_prop_invoice_receipt (receipt_id)
) engine=InnoDB default charset=utf8mb4 comment='物业电子发票申请';
