create table if not exists bp_role_action (
  role_id bigint not null,
  action_code varchar(128) not null,
  primary key (role_id, action_code)
) engine=InnoDB default charset=utf8mb4 comment='角色功能/操作权限';
