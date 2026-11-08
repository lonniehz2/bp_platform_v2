-- 智慧物业 V1 退款记录
create table if not exists prop_refund (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  refund_no varchar(64) not null,
  biz_type varchar(32) not null,
  biz_id bigint null,
  payment_id bigint null,
  plan_id bigint null,
  amount decimal(14,2) not null,
  reason varchar(500) null,
  refund_status varchar(20) not null default 'PENDING',
  refund_time datetime null,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_refund_no (tenant_id, refund_no),
  key idx_prop_refund_project (tenant_id, project_id, create_time)
) engine=InnoDB default charset=utf8mb4 comment='物业退款记录';
