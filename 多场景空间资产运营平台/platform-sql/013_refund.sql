-- 账单退款（已有库升级用）

create table if not exists bp_refund (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  refund_no varchar(64) not null,
  payment_id bigint not null,
  bill_id bigint not null,
  allocation_id bigint not null,
  amount decimal(14,2) not null,
  reason varchar(500),
  refund_status varchar(32) not null default 'SUCCESS',
  refunded_time datetime,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_refund_no (tenant_id,refund_no),
  key idx_refund_payment (tenant_id,payment_id),
  key idx_refund_bill (tenant_id,bill_id)
) engine=InnoDB default charset=utf8mb4 comment='账单退款';
