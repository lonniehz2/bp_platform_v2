-- 电子收款凭证模板与验真
create table if not exists bp_receipt_template (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  template_name varchar(128) not null,
  config_json text not null,
  version int not null default 1,
  status varchar(20) not null default 'DRAFT',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp
) engine=InnoDB default charset=utf8mb4 comment='收款凭证模板';

create table if not exists bp_receipt_document (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  receipt_id bigint not null,
  project_id bigint null,
  template_id bigint null,
  template_version int not null default 1,
  verify_token varchar(64) not null,
  verify_code varchar(16) not null,
  pdf_sha256 varchar(64) null,
  document_status varchar(20) not null default 'VALID',
  signed_time datetime null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_receipt_document_receipt (receipt_id),
  unique key uk_receipt_document_token (verify_token),
  key idx_receipt_document_code (verify_code)
) engine=InnoDB default charset=utf8mb4 comment='收款凭证文档与验真';
