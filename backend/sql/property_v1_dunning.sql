-- 智慧物业 V1 欠费催缴
create table if not exists prop_dunning_task (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  task_no varchar(64) not null,
  channels varchar(64) not null,
  reason varchar(500) null,
  task_status varchar(20) not null default 'SENT',
  total_count int not null default 0,
  success_count int not null default 0,
  fail_count int not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  key idx_prop_dunning_project (tenant_id, project_id, create_time)
) engine=InnoDB default charset=utf8mb4 comment='物业催缴任务';

create table if not exists prop_dunning_record (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  task_id bigint not null,
  bill_id bigint not null,
  person_id bigint null,
  payer_name varchar(128) null,
  house_name varchar(128) null,
  amount decimal(14,2) not null,
  channel varchar(20) not null,
  recipient varchar(128) null,
  content varchar(1000) null,
  send_status varchar(20) not null default 'SENT',
  send_time datetime null,
  error_msg varchar(500) null,
  create_time datetime not null default current_timestamp,
  key idx_prop_dunning_record_task (task_id)
) engine=InnoDB default charset=utf8mb4 comment='物业催缴记录';
