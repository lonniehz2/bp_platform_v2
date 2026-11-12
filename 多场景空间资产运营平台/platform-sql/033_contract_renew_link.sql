alter table guarantee_contract add column renew_from_id bigint null comment '续签来源合同';
alter table guarantee_contract add column renew_to_id bigint null comment '续签生成合同';
