-- 智慧物业 V1 租户域名
create table if not exists bp_iam_tenant_domain (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  domain varchar(128) not null,
  is_primary tinyint not null default 0,
  status varchar(20) not null default 'ENABLED',
  create_time datetime not null default current_timestamp,
  unique key uk_tenant_domain (domain),
  key idx_tenant_domain_tenant (tenant_id)
) engine=InnoDB default charset=utf8mb4 comment='租户登录域名';

insert ignore into bp_iam_tenant_domain(id, tenant_id, domain, is_primary, status)
values (800000000000004001, '350600', 'demo', 1, 'ENABLED');
