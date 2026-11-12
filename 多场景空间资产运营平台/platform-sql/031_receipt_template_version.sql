create table if not exists bp_receipt_template_version (
 id bigint not null primary key,
 tenant_id varchar(32) not null,
 template_id bigint not null,
 config_json text not null,
 version int not null,
 create_time datetime not null default current_timestamp,
 key idx_receipt_template_version (template_id, version)
) engine=InnoDB default charset=utf8mb4 comment='收据模板版本历史';
