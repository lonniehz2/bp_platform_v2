-- 角色默认数据范围与用户例外
create table if not exists bp_role_scope (
  role_id bigint not null primary key,
  tenant_id varchar(32) not null,
  scope_type varchar(20) not null default 'NONE',
  update_time datetime not null default current_timestamp on update current_timestamp
) engine=InnoDB default charset=utf8mb4 comment='角色默认数据范围';

create table if not exists bp_role_project (
  role_id bigint not null,
  project_id bigint not null,
  primary key (role_id, project_id)
) engine=InnoDB default charset=utf8mb4 comment='角色默认项目范围';

create table if not exists bp_role_org (
  role_id bigint not null,
  org_id bigint not null,
  primary key (role_id, org_id)
) engine=InnoDB default charset=utf8mb4 comment='角色默认组织范围';

create table if not exists bp_user_scope_override (
  user_id bigint not null primary key,
  tenant_id varchar(32) not null,
  enabled tinyint not null default 0,
  update_time datetime not null default current_timestamp on update current_timestamp
) engine=InnoDB default charset=utf8mb4 comment='用户数据范围例外开关';
