-- 房源预约转订单

create table if not exists bp_listing_order (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  listing_id bigint not null,
  booking_id bigint not null,
  person_id bigint not null,
  order_no varchar(64) not null,
  order_status varchar(20) not null default 'CONFIRMED',
  rent_amount decimal(14,2) not null,
  deposit_amount decimal(14,2) not null default 0,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_listing_order_no (tenant_id,order_no),
  unique key uk_listing_order_booking (tenant_id,booking_id)
) engine=InnoDB default charset=utf8mb4 comment='房源预约转订单';
