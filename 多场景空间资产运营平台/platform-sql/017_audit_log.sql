-- 操作审计日志

create table if not exists bp_audit_log (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  user_id bigint,
  username varchar(64),
  method varchar(10),
  path varchar(500),
  status_code int,
  ip varchar(64),
  create_time datetime not null default current_timestamp,
  key idx_audit_time (tenant_id,id),
  key idx_audit_user (tenant_id,user_id)
) engine=InnoDB default charset=utf8mb4 comment='操作审计日志';
