-- 智慧物业 V1 业主/住户与房屋关系
create table if not exists prop_owner_unit (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint not null,
  person_id bigint not null,
  relation_type varchar(20) not null default 'OWNER',
  is_primary tinyint not null default 0,
  share_ratio decimal(5,2) null,
  start_date date null,
  end_date date null,
  status varchar(20) not null default 'ACTIVE',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_owner_house (tenant_id, house_id, status),
  key idx_prop_owner_person (tenant_id, person_id)
) engine=InnoDB default charset=utf8mb4 comment='物业业主/住户与房屋关系';
