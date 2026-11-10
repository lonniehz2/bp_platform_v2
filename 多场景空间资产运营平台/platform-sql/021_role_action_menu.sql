-- 操作权限改为页面级：role_id + menu_code + action_code
drop table if exists bp_role_action;
create table bp_role_action (
  role_id bigint not null,
  menu_code varchar(64) not null,
  action_code varchar(32) not null,
  primary key (role_id, menu_code, action_code),
  key idx_role_action_menu (menu_code)
) engine=InnoDB default charset=utf8mb4 comment='角色页面操作权限';
