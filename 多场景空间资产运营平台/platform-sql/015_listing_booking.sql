-- 房源展示与看房预约

create table if not exists bp_listing (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint not null,
  title varchar(200) not null,
  description varchar(1000),
  monthly_rent decimal(14,2) not null,
  deposit_amount decimal(14,2) not null default 0,
  listing_status varchar(20) not null default 'DRAFT',
  publish_time datetime,
  cover_url varchar(500),
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_listing_house (tenant_id,house_id)
) engine=InnoDB default charset=utf8mb4 comment='房源展示';

create table if not exists bp_booking (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  listing_id bigint not null,
  person_id bigint not null,
  booking_no varchar(64) not null,
  booking_status varchar(20) not null default 'PENDING',
  contact_phone varchar(32),
  remark varchar(500),
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_booking_no (tenant_id,booking_no),
  key idx_booking_listing (tenant_id,listing_id)
) engine=InnoDB default charset=utf8mb4 comment='看房预约';
