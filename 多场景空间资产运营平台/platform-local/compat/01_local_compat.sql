-- 本地全新库兼容补丁：001 基础 schema 之后的当前应用字段
alter table bp_listing_order add column payment_status varchar(20) not null default 'UNPAID';
alter table bp_listing_order add column contract_id bigint null;

create table if not exists bp_listing_payment (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  order_id bigint not null,
  payment_no varchar(64) not null,
  amount decimal(14,2) not null,
  payment_method varchar(32) null,
  payment_status varchar(20) not null default 'SUCCESS',
  paid_time datetime not null default current_timestamp,
  is_deleted tinyint not null default 0,
  unique key uk_listing_payment_no (tenant_id,payment_no)
) engine=InnoDB default charset=utf8mb4;
