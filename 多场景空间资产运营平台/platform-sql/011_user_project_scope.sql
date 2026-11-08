-- 用户项目数据范围（已有库升级用）
-- 新库 001_platform_core.sql 已包含该表。

create table if not exists bp_user_project (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  user_id bigint not null,
  project_id bigint not null,
  is_default tinyint not null default 0,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_user_project (tenant_id,user_id,project_id),
  key idx_user_project_user (tenant_id,user_id)
) engine=InnoDB default charset=utf8mb4 comment='用户项目数据范围';
