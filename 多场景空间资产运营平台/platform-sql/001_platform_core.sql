-- 多场景空间资产运营平台：平台核心 Schema
-- 数据库：bp_platform_v2
-- 状态：Phase 0 框架草案，先用于本地验证

create table if not exists bp_tenant (
  id bigint not null primary key,
  tenant_code varchar(32) not null,
  tenant_name varchar(128) not null,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_tenant_code (tenant_code)
) engine=InnoDB default charset=utf8mb4 comment='平台租户';

create table if not exists bp_scene_profile (
  id bigint not null primary key,
  scene_code varchar(32) not null,
  scene_name varchar(128) not null,
  sort_no int not null default 0,
  status varchar(20) not null default 'ENABLED',
  create_time datetime not null default current_timestamp,
  unique key uk_bp_scene_code (scene_code)
) engine=InnoDB default charset=utf8mb4 comment='场景包';

create table if not exists bp_business_mode (
  id bigint not null primary key,
  scene_code varchar(32) not null,
  mode_code varchar(32) not null,
  mode_name varchar(128) not null,
  sort_no int not null default 0,
  status varchar(20) not null default 'ENABLED',
  create_time datetime not null default current_timestamp,
  unique key uk_bp_business_mode (scene_code, mode_code),
  key idx_bp_business_mode_scene (scene_code, status)
) engine=InnoDB default charset=utf8mb4 comment='经营模式';

create table if not exists bp_tenant_scene (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  scene_code varchar(32) not null,
  status varchar(20) not null default 'ENABLED',
  create_time datetime not null default current_timestamp,
  unique key uk_bp_tenant_scene (tenant_id, scene_code)
) engine=InnoDB default charset=utf8mb4 comment='租户启用场景';

create table if not exists bp_org (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  parent_id bigint null,
  org_code varchar(64) not null,
  org_name varchar(128) not null,
  org_type varchar(32) not null,
  scene_code varchar(32) null,
  business_mode varchar(32) null,
  space_template_id bigint null,
  default_asset_type_code varchar(64) null,
  address varchar(255) null,
  contact_name varchar(64) null,
  contact_phone varchar(32) null,
  remark varchar(500) null,
  total_area decimal(12,2) null,
  land_area decimal(12,2) null,
  property_type varchar(32) null,
  build_year int null,
  org_path varchar(500) null,
  sort_no int not null default 0,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_org_code (tenant_id, org_code),
  key idx_bp_org_parent (tenant_id, parent_id),
  key idx_bp_org_scene (tenant_id, scene_code, business_mode)
) engine=InnoDB default charset=utf8mb4 comment='平台组织/项目';

create table if not exists bp_space_template (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  scene_code varchar(32) not null,
  template_code varchar(64) not null,
  template_name varchar(128) not null,
  asset_type_code varchar(64) null,
  base_level_count int not null,
  level_count int not null,
  levels_json json not null,
  allowed_sub_modes varchar(128) null,
  is_system tinyint not null default 0,
  version_no int not null default 1,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_space_template (tenant_id, template_code, version_no),
  key idx_bp_space_template_scene (tenant_id, scene_code, status)
) engine=InnoDB default charset=utf8mb4 comment='空间结构模板';

create table if not exists bp_asset_type (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  scene_code varchar(32) not null,
  type_code varchar(64) not null,
  type_name varchar(128) not null,
  type_category varchar(32) not null,
  sort_no int not null default 0,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_asset_type (tenant_id, scene_code, type_code),
  key idx_bp_asset_type_scene (tenant_id, scene_code, type_category, status)
) engine=InnoDB default charset=utf8mb4 comment='资产类型字典';

create table if not exists bp_space (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  org_id bigint not null,
  parent_id bigint null,
  space_code varchar(64) not null,
  space_name varchar(128) not null,
  space_type varchar(32) not null,
  space_path varchar(1000) null,
  level_no int not null default 1,
  asset_type_code varchar(64) null,
  space_template_id bigint null,
  business_mode varchar(32) null,
  sub_unit_mode varchar(20) null,
  area decimal(14,2) null,
  sort_no int not null default 0,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_space_code (tenant_id, org_id, space_code),
  key idx_bp_space_parent (tenant_id, org_id, parent_id),
  key idx_bp_space_type (tenant_id, org_id, space_type)
) engine=InnoDB default charset=utf8mb4 comment='空间节点';

create table if not exists bp_house (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  org_id bigint not null,
  space_id bigint not null,
  house_code varchar(64) not null,
  house_name varchar(128) not null,
  asset_type_code varchar(64) null,
  area decimal(14,2) null,
  inner_area decimal(14,2) null,
  house_status varchar(20) not null default 'PENDING',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_house_space (tenant_id, space_id),
  unique key uk_bp_house_code (tenant_id, org_id, house_code)
) engine=InnoDB default charset=utf8mb4 comment='房屋/可租资产';

create table if not exists bp_person (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  org_id bigint null,
  person_code varchar(64) not null,
  person_name varchar(128) not null,
  phone varchar(32) null,
  id_card_mask varchar(32) null,
  person_type varchar(32) null,
  gender varchar(10) null,
  birth_date date null,
  address varchar(255) null,
  employer varchar(128) null,
  emergency_contact varchar(128) null,
  remark varchar(500) null,
  verify_status varchar(20) not null default 'UNVERIFIED',
  face_photo_url varchar(500) null,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_person_code (tenant_id, person_code)
) engine=InnoDB default charset=utf8mb4 comment='人员主档';

create table if not exists bp_person_relation (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  person_id bigint not null,
  project_id bigint not null,
  target_type varchar(20) not null,
  target_id bigint not null,
  relation_type varchar(32) not null,
  is_primary tinyint not null default 0,
  start_date date null,
  end_date date null,
  status varchar(20) not null default 'ACTIVE',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_bp_person_relation_person (tenant_id, person_id, status),
  key idx_bp_person_relation_target (tenant_id, target_type, target_id, status)
) engine=InnoDB default charset=utf8mb4 comment='人员与项目/空间/房屋关系';

-- 场景
insert ignore into bp_scene_profile(id, scene_code, scene_name, sort_no)
values
(910000000000000001,'GUARANTEE','保障房',10),
(910000000000000002,'PROPERTY','物业',20),
(910000000000000003,'APARTMENT','公寓',30),
(910000000000000004,'OFFICE','办公楼',40),
(910000000000000005,'HOTEL','酒店',50),
(910000000000000006,'BNB','民宿',60),
(910000000000000007,'ONLINE_RENTAL','网约房',70),
(910000000000000008,'DORMITORY','宿舍',80),
(910000000000000009,'CAMPUS','校园',90);

insert ignore into bp_business_mode(id, scene_code, mode_code, mode_name, sort_no)
values
(910000000000001001,'GUARANTEE','PUBLIC_RENTAL','公租房',1),
(910000000000001002,'GUARANTEE','AFFORDABLE_RENTAL','保租房',2),
(910000000000001003,'GUARANTEE','TALENT_APARTMENT','人才公寓',3),
(910000000000001004,'GUARANTEE','DORMITORY','宿舍',4),
(910000000000001005,'GUARANTEE','OTHER','其他',9),
(910000000000001011,'PROPERTY','RESIDENTIAL','住宅物业',1),
(910000000000001012,'PROPERTY','COMMERCIAL','商业物业',2),
(910000000000001013,'PROPERTY','OFFICE','办公楼物业',3),
(910000000000001014,'PROPERTY','MIXED_USE','混合业态',4),
(910000000000001021,'APARTMENT','WHOLE_RENT','整租公寓',1),
(910000000000001022,'APARTMENT','SHARED_RENT','合租公寓',2),
(910000000000001023,'APARTMENT','SERVICED_APARTMENT','服务式公寓',3),
(910000000000001031,'HOTEL','HOTEL','酒店',1),
(910000000000001041,'BNB','BNB','民宿',1),
(910000000000001051,'ONLINE_RENTAL','ONLINE_RENTAL','网约房',1),
(910000000000001061,'DORMITORY','DORMITORY','宿舍',1),
(910000000000001071,'CAMPUS','CAMPUS','校园',1);

insert ignore into bp_tenant(id, tenant_code, tenant_name)
values (1,'350600','演示租户');

insert ignore into bp_tenant_scene(id, tenant_id, scene_code)
values
(910000000000002001,'350600','GUARANTEE'),
(910000000000002002,'350600','PROPERTY'),
(910000000000002003,'350600','APARTMENT'),
(910000000000002004,'350600','OFFICE'),
(910000000000002005,'350600','HOTEL'),
(910000000000002006,'350600','BNB'),
(910000000000002007,'350600','ONLINE_RENTAL'),
(910000000000002008,'350600','DORMITORY'),
(910000000000002009,'350600','CAMPUS');

-- 模板
insert ignore into bp_space_template
(id, tenant_id, scene_code, template_code, template_name, base_level_count, level_count, levels_json, allowed_sub_modes, is_system)
values
(910000000000003001,'350600','GUARANTEE','GUARANTEE_BASE','保障房基础',
 5,5,
 JSON_ARRAY(
   JSON_OBJECT('level',1,'name','小区','required',true),
   JSON_OBJECT('level',2,'name','楼栋','required',true),
   JSON_OBJECT('level',3,'name','单元','required',false),
   JSON_OBJECT('level',4,'name','楼层','required',true),
   JSON_OBJECT('level',5,'name','房屋','required',true)
 ),
 'NONE,BED,INNER_ROOM,INNER_ROOM_BED',1),
(910000000000003002,'350600','PROPERTY','PROPERTY_RESIDENTIAL','住宅物业',
 6,6,
 JSON_ARRAY(
   JSON_OBJECT('level',1,'name','期','required',false),
   JSON_OBJECT('level',2,'name','苑/幢','required',true),
   JSON_OBJECT('level',3,'name','单元','required',false),
   JSON_OBJECT('level',4,'name','楼层','required',true),
   JSON_OBJECT('level',5,'name','房号','required',true),
   JSON_OBJECT('level',6,'name','子房号','required',false)
 ),
 'NONE,INNER_ROOM',1);

-- 资产类型
insert ignore into bp_asset_type(id,tenant_id,scene_code,type_code,type_name,type_category,sort_no)
values
(910000000000004001,'350600','GUARANTEE','PUBLIC_RENTAL','公租房','HOUSE',1),
(910000000000004002,'350600','GUARANTEE','AFFORDABLE_RENTAL','保租房','HOUSE',2),
(910000000000004003,'350600','GUARANTEE','TALENT_APARTMENT','人才公寓','HOUSE',3),
(910000000000004004,'350600','GUARANTEE','DORMITORY','宿舍','HOUSE',4),
(910000000000004005,'350600','GUARANTEE','BED','床位','BED',5),
(910000000000004006,'350600','GUARANTEE','INNER_ROOM','内房','INNER_ROOM',6),
(910000000000004011,'350600','PROPERTY','RES_HIGH_RISE','高层住宅','HOUSE',1),
(910000000000004012,'350600','PROPERTY','RES_MULTI','多层住宅','HOUSE',2),
(910000000000004013,'350600','PROPERTY','RES_TOWNHOUSE','排屋','HOUSE',3),
(910000000000004014,'350600','PROPERTY','COMMERCIAL','商业','HOUSE',4),
(910000000000004015,'350600','PROPERTY','SHOP','商铺','HOUSE',5),
(910000000000004016,'350600','PROPERTY','OFFICE','办公','HOUSE',6),
(910000000000004017,'350600','PROPERTY','PARKING_GARAGE','车库车位','PARKING',7),
(910000000000004018,'350600','PROPERTY','PARKING_OPEN','露天车位','PARKING',8);


-- =========================================================
-- 保障房合同与平台计费内核
-- =========================================================

create table if not exists guarantee_contract (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_no varchar(64) not null,
  house_id bigint not null,
  person_id bigint not null,
  start_date date not null,
  end_date date not null,
  rent_amount decimal(14,2) not null default 0,
  deposit_amount decimal(14,2) not null default 0,
  billing_cycle varchar(20) not null default 'MONTH',
  bill_day int not null default 1,
  contract_status varchar(20) not null default 'ACTIVE',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_contract_no (tenant_id, contract_no),
  key idx_guarantee_contract_project (tenant_id, project_id, contract_status),
  key idx_guarantee_contract_house (tenant_id, house_id, contract_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房租赁合同';

create table if not exists bp_bill (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  bill_no varchar(64) not null,
  biz_type varchar(32) not null,
  contract_type varchar(32) null,
  contract_id bigint null,
  house_id bigint null,
  person_id bigint null,
  fee_item_code varchar(64) not null,
  period_start date not null,
  period_end date not null,
  amount decimal(14,2) not null,
  discount_amount decimal(14,2) not null default 0,
  payable_amount decimal(14,2) null,
  paid_amount decimal(14,2) not null default 0,
  bill_status varchar(20) not null default 'UNPAID',
  due_date date null,
  source_type varchar(20) null,
  source_id bigint null,
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_bill_no (tenant_id, bill_no),
  unique key uk_bp_bill_contract_period (tenant_id, contract_id, period_start, period_end),
  key idx_bp_bill_project (tenant_id, project_id, bill_status),
  key idx_bp_bill_person (tenant_id, person_id, bill_status)
) engine=InnoDB default charset=utf8mb4 comment='平台账单';

create table if not exists bp_payment (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  payment_no varchar(64) not null,
  payer_person_id bigint null,
  amount decimal(14,2) not null,
  payment_method varchar(32) not null default 'CASH',
  payment_status varchar(20) not null default 'SUCCESS',
  paid_time datetime not null default current_timestamp,
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_bp_payment_no (tenant_id, payment_no),
  key idx_bp_payment_project (tenant_id, project_id, payment_status)
) engine=InnoDB default charset=utf8mb4 comment='平台收款';

create table if not exists bp_payment_allocation (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  payment_id bigint not null,
  bill_id bigint not null,
  amount decimal(14,2) not null,
  create_time datetime not null default current_timestamp,
  unique key uk_bp_payment_allocation (tenant_id, payment_id, bill_id),
  key idx_bp_payment_allocation_bill (tenant_id, bill_id)
) engine=InnoDB default charset=utf8mb4 comment='收款分摊';

create table if not exists bp_receipt (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  receipt_no varchar(64) not null,
  payment_id bigint not null,
  amount decimal(14,2) not null,
  receipt_status varchar(20) not null default 'ISSUED',
  issued_time datetime not null default current_timestamp,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_bp_receipt_no (tenant_id, receipt_no),
  unique key uk_bp_receipt_payment (tenant_id, payment_id)
) engine=InnoDB default charset=utf8mb4 comment='收据';


-- =========================================================
-- 平台审批/工作流
-- =========================================================

create table if not exists bp_wf_flow (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  scene_code varchar(32) not null,
  biz_type varchar(32) not null,
  flow_name varchar(128) not null,
  flow_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_bp_wf_flow (tenant_id, scene_code, biz_type, flow_name)
) engine=InnoDB default charset=utf8mb4 comment='审批流程';

create table if not exists bp_wf_node (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  flow_id bigint not null,
  node_seq int not null,
  node_name varchar(128) not null,
  approver_role varchar(64) null,
  node_status varchar(20) not null default 'ENABLED',
  unique key uk_bp_wf_node (tenant_id, flow_id, node_seq)
) engine=InnoDB default charset=utf8mb4 comment='审批节点';

create table if not exists bp_wf_task (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint null,
  biz_type varchar(32) not null,
  biz_id bigint not null,
  flow_id bigint not null,
  current_node_id bigint null,
  task_status varchar(20) not null default 'APPROVING',
  submitter_name varchar(64) null,
  amount decimal(14,2) null,
  summary varchar(500) null,
  submit_time datetime not null default current_timestamp,
  finish_time datetime null,
  is_deleted tinyint not null default 0,
  unique key uk_bp_wf_task_biz (tenant_id, biz_type, biz_id),
  key idx_bp_wf_task_status (tenant_id, project_id, task_status)
) engine=InnoDB default charset=utf8mb4 comment='审批任务';

create table if not exists bp_wf_record (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  task_id bigint not null,
  node_id bigint not null,
  approver_name varchar(64) null,
  action varchar(20) not null,
  comment_text varchar(500) null,
  action_time datetime not null default current_timestamp,
  key idx_bp_wf_record_task (tenant_id, task_id, action_time)
) engine=InnoDB default charset=utf8mb4 comment='审批记录';


create table if not exists guarantee_contract_change (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_id bigint not null,
  change_type varchar(32) not null,
  before_json json null,
  after_json json null,
  effective_date date null,
  change_status varchar(20) not null default 'DRAFT',
  reason varchar(500) null,
  workflow_task_id bigint null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_change_contract (tenant_id, contract_id, change_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房合同变更/退租';


create table if not exists guarantee_application (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  application_no varchar(64) not null,
  applicant_person_id bigint not null,
  application_type varchar(32) not null default 'PUBLIC_RENTAL',
  family_size int not null default 1,
  contact_phone varchar(32) null,
  income_level varchar(32) null,
  housing_status varchar(32) null,
  urgency varchar(20) null,
  remark varchar(500) null,
  guarantee_type varchar(32) null,
  family_type varchar(32) null,
  subsidy_status varchar(32) null,
  archive_no varchar(64) null,
  application_status varchar(20) not null default 'DRAFT',
  submit_time datetime null,
  review_time datetime null,
  review_comment varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_application_no (tenant_id, application_no),
  key idx_guarantee_application_project (tenant_id, project_id, application_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房申请';

create table if not exists guarantee_waitlist (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  application_id bigint not null,
  queue_no varchar(32) not null,
  waitlist_status varchar(20) not null default 'WAITING',
  joined_time datetime not null default current_timestamp,
  is_deleted tinyint not null default 0,
  unique key uk_guarantee_waitlist_application (tenant_id, application_id),
  key idx_guarantee_waitlist_project (tenant_id, project_id, waitlist_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房轮候';

create table if not exists guarantee_allocation (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  application_id bigint not null,
  house_id bigint not null,
  allocation_no varchar(64) not null,
  allocation_status varchar(20) not null default 'ALLOCATED',
  contract_id bigint null,
  allocated_time datetime not null default current_timestamp,
  is_deleted tinyint not null default 0,
  unique key uk_guarantee_allocation_application (tenant_id, application_id),
  unique key uk_guarantee_allocation_no (tenant_id, allocation_no),
  key idx_guarantee_allocation_house (tenant_id, house_id, allocation_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房配租';


create table if not exists guarantee_deposit (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_id bigint not null,
  person_id bigint not null,
  amount decimal(14,2) not null default 0,
  paid_amount decimal(14,2) not null default 0,
  refunded_amount decimal(14,2) not null default 0,
  deposit_status varchar(20) not null default 'PENDING',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_deposit_contract (tenant_id, contract_id),
  key idx_guarantee_deposit_project (tenant_id, project_id, deposit_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房押金';

create table if not exists guarantee_deposit_txn (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  deposit_id bigint not null,
  txn_type varchar(20) not null,
  amount decimal(14,2) not null,
  operator_name varchar(64) null,
  remark varchar(500) null,
  txn_time datetime not null default current_timestamp,
  key idx_guarantee_deposit_txn (tenant_id, deposit_id, txn_time)
) engine=InnoDB default charset=utf8mb4 comment='保障房押金流水';


create table if not exists guarantee_subsidy (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_id bigint not null,
  subsidy_type varchar(32) not null default 'RENT_SUBSIDY',
  subsidy_amount decimal(14,2) not null default 0,
  start_date date not null,
  end_date date not null,
  subsidy_status varchar(20) not null default 'ACTIVE',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_subsidy_contract (tenant_id, contract_id, subsidy_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房补贴';


create table if not exists bp_dev_device (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  space_id bigint null,
  device_code varchar(64) not null,
  device_name varchar(128) not null,
  device_type varchar(64) not null,
  device_model varchar(128) null,
  asset_status varchar(20) not null default 'ACTIVE',
  business_status varchar(20) not null default 'IN_USE',
  install_time datetime null,
  warranty_end date null,
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_dev_device_code (tenant_id, device_code),
  key idx_bp_dev_device_project (tenant_id, project_id, asset_status),
  key idx_bp_dev_device_space (tenant_id, space_id)
) engine=InnoDB default charset=utf8mb4 comment='设备业务资产';

create table if not exists bp_grant_entitlement (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  person_id bigint not null,
  target_type varchar(20) not null,
  target_id bigint not null,
  grant_level varchar(20) not null default 'OPEN',
  valid_start date not null,
  valid_end date null,
  grant_status varchar(20) not null default 'ACTIVE',
  source_type varchar(20) null,
  source_id bigint null,
  revoke_reason varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_bp_grant_person (tenant_id, person_id, grant_status),
  key idx_bp_grant_target (tenant_id, target_type, target_id, grant_status)
) engine=InnoDB default charset=utf8mb4 comment='人员空间/设备授权';


create table if not exists bp_role (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  scene_code varchar(32) not null,
  role_code varchar(64) not null,
  role_name varchar(128) not null,
  role_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_bp_role_code (tenant_id, scene_code, role_code)
) engine=InnoDB default charset=utf8mb4 comment='场景角色模板';

create table if not exists bp_menu (
  id bigint not null primary key,
  scene_code varchar(32) not null,
  menu_code varchar(64) not null,
  parent_code varchar(64) null,
  menu_name varchar(128) not null,
  menu_type varchar(20) not null default 'MENU',
  route varchar(255) null,
  sort_no int not null default 0,
  menu_status varchar(20) not null default 'ENABLED',
  unique key uk_bp_menu_code (scene_code, menu_code)
) engine=InnoDB default charset=utf8mb4 comment='场景菜单';

create table if not exists bp_role_menu (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  role_id bigint not null,
  menu_id bigint not null,
  unique key uk_bp_role_menu (tenant_id, role_id, menu_id)
) engine=InnoDB default charset=utf8mb4 comment='角色菜单';


create table if not exists bp_user (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  username varchar(64) not null,
  password_hash varchar(200) not null,
  display_name varchar(128) not null,
  user_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_user_username (tenant_id, username)
) engine=InnoDB default charset=utf8mb4 comment='平台用户';

create table if not exists bp_user_role (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  user_id bigint not null,
  role_id bigint not null,
  unique key uk_bp_user_role (tenant_id, user_id, role_id)
) engine=InnoDB default charset=utf8mb4 comment='用户角色';


create table if not exists guarantee_qualification_review (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_id bigint not null,
  person_id bigint not null,
  review_type varchar(20) not null default 'ANNUAL',
  review_year int not null,
  review_status varchar(20) not null default 'PENDING',
  review_date date null,
  reviewer_name varchar(64) null,
  review_comment varchar(500) null,
  next_review_date date null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_review (tenant_id, contract_id, review_type, review_year),
  key idx_guarantee_review_project (tenant_id, project_id, review_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房资格复核';


create table if not exists bp_migration_exception (
  id bigint not null primary key,
  source_table varchar(64) not null,
  source_id bigint not null,
  reason varchar(500) not null,
  payload varchar(2000) null,
  resolve_status varchar(20) not null default 'PENDING',
  resolution varchar(500) null,
  resolved_by varchar(64) null,
  resolved_time datetime null,
  create_time datetime not null default current_timestamp,
  unique key uk_bp_migration_exception (source_table, source_id)
) engine=InnoDB default charset=utf8mb4 comment='老数据迁移异常';


create table if not exists bp_file (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  biz_type varchar(32) not null,
  biz_id bigint not null,
  file_name varchar(255) not null,
  content_type varchar(128) null,
  file_size bigint not null default 0,
  storage_path varchar(500) not null,
  uploader varchar(64) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  key idx_bp_file_biz (tenant_id, biz_type, biz_id)
) engine=InnoDB default charset=utf8mb4 comment='平台附件';


create table if not exists guarantee_subsidy_standard (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint null,
  standard_code varchar(64) not null,
  standard_name varchar(128) not null,
  security_type varchar(32) null,
  income_level varchar(32) null,
  family_type varchar(32) null,
  talent_level varchar(32) null,
  subsidy_mode varchar(32) null,
  subsidy_value decimal(14,2) null,
  max_amount decimal(14,2) null,
  effective_start date null,
  effective_end date null,
  standard_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_guarantee_subsidy_standard (tenant_id, standard_code)
) engine=InnoDB default charset=utf8mb4 comment='保障房补贴标准';


create table if not exists guarantee_meter (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint not null,
  meter_type varchar(20) not null,
  meter_no varchar(64) not null,
  initial_reading decimal(14,2) not null default 0,
  current_reading decimal(14,2) not null default 0,
  install_date date null,
  meter_status varchar(20) not null default 'ACTIVE',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_meter_no (tenant_id, meter_no),
  key idx_guarantee_meter_project (tenant_id, project_id, meter_type, meter_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房表计';

create table if not exists guarantee_meter_reading (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  meter_id bigint not null,
  reading_date date not null,
  reading_value decimal(14,2) not null,
  previous_value decimal(14,2) not null,
  usage_amount decimal(14,2) not null,
  reader_name varchar(64) null,
  create_time datetime not null default current_timestamp,
  key idx_guarantee_meter_reading (tenant_id, meter_id, reading_date)
) engine=InnoDB default charset=utf8mb4 comment='保障房抄表记录';


create table if not exists guarantee_work_order (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  order_no varchar(64) not null,
  order_type varchar(20) not null default 'REPAIR',
  title varchar(200) not null,
  description varchar(1000) null,
  house_id bigint null,
  person_id bigint null,
  priority varchar(20) not null default 'NORMAL',
  order_status varchar(20) not null default 'PENDING',
  assignee_name varchar(64) null,
  finish_time datetime null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_work_order_no (tenant_id, order_no),
  key idx_guarantee_work_order_project (tenant_id, project_id, order_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房服务工单';


create table if not exists guarantee_access_record (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint null,
  person_id bigint null,
  visitor_name varchar(128) not null,
  visitor_phone varchar(32) null,
  purpose varchar(200) null,
  valid_start datetime null,
  valid_end datetime null,
  access_status varchar(20) not null default 'PENDING',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_access_project (tenant_id, project_id, access_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房访客通行登记';


create table if not exists guarantee_complaint (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  complaint_type varchar(20) not null default 'COMPLAINT',
  title varchar(200) not null,
  content varchar(2000) null,
  house_id bigint null,
  person_id bigint null,
  complaint_status varchar(20) not null default 'PENDING',
  handler_name varchar(64) null,
  handle_result varchar(1000) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_complaint_project (tenant_id, project_id, complaint_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房投诉申诉走访';


create table if not exists guarantee_fee_item (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  fee_code varchar(64) not null,
  fee_name varchar(128) not null,
  fee_type varchar(20) not null default 'OTHER',
  billing_cycle varchar(20) not null default 'MONTHLY',
  unit_price decimal(14,2) not null default 0,
  unit_name varchar(32) null,
  tax_rate decimal(6,4) not null default 0,
  fee_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_fee_item (tenant_id, project_id, fee_code)
) engine=InnoDB default charset=utf8mb4 comment='保障房计费项目';


create table if not exists guarantee_publicity (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  publicity_type varchar(20) not null default 'ALLOCATION',
  title varchar(200) not null,
  content varchar(2000) null,
  start_date date null,
  end_date date null,
  publicity_status varchar(20) not null default 'DRAFT',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_publicity_project (tenant_id, project_id, publicity_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房公示';


create table if not exists guarantee_alert (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  alert_type varchar(20) not null default 'RISK',
  alert_level varchar(20) not null default 'NORMAL',
  title varchar(200) not null,
  content varchar(2000) null,
  house_id bigint null,
  person_id bigint null,
  alert_status varchar(20) not null default 'PENDING',
  handler_name varchar(64) null,
  handle_result varchar(1000) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_alert_project (tenant_id, project_id, alert_status, alert_level)
) engine=InnoDB default charset=utf8mb4 comment='保障房风险告警';


create table if not exists guarantee_credit_record (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  person_id bigint not null,
  credit_type varchar(20) not null default 'VIOLATION',
  score_change int not null default 0,
  reason varchar(500) null,
  record_status varchar(20) not null default 'ACTIVE',
  effective_date date null,
  expire_date date null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_credit_project (tenant_id, project_id, record_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房信用记录';


create table if not exists guarantee_short_rent_order (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint null,
  order_no varchar(64) not null,
  guest_name varchar(128) not null,
  guest_phone varchar(32) null,
  start_date date not null,
  end_date date not null,
  nights int not null default 1,
  amount decimal(14,2) not null default 0,
  order_status varchar(20) not null default 'PENDING',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_short_rent_no (tenant_id, order_no),
  key idx_guarantee_short_rent_project (tenant_id, project_id, order_status)
) engine=InnoDB default charset=utf8mb4 comment='保障房短租订单';


create table if not exists guarantee_open_app (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  app_code varchar(64) not null,
  app_name varchar(128) not null,
  app_secret varchar(128) not null,
  scopes varchar(500) null,
  app_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_guarantee_open_app (tenant_id, app_code)
) engine=InnoDB default charset=utf8mb4 comment='保障房开放平台应用';


create table if not exists bp_message (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  user_id bigint null,
  title varchar(200) not null,
  content varchar(2000) null,
  biz_type varchar(32) null,
  biz_id varchar(64) null,
  read_status varchar(20) not null default 'UNREAD',
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  key idx_bp_message_user (tenant_id, user_id, read_status, create_time)
) engine=InnoDB default charset=utf8mb4 comment='平台消息';


create table if not exists guarantee_contract_cohabitant (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  contract_id bigint not null,
  person_id bigint not null,
  relation_type varchar(32) not null default 'FAMILY',
  is_primary tinyint not null default 0,
  start_date date null,
  end_date date null,
  cohabitant_status varchar(20) not null default 'ACTIVE',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_guarantee_cohabitant_contract (tenant_id, contract_id, cohabitant_status)
) engine=InnoDB default charset=utf8mb4 comment='合同同住人';


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


create table if not exists bp_user_org (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  user_id bigint not null,
  org_id bigint not null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_user_org (tenant_id,user_id,org_id),
  key idx_user_org_user (tenant_id,user_id)
) engine=InnoDB default charset=utf8mb4 comment='用户组织数据范围';


create table if not exists bp_refund (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  refund_no varchar(64) not null,
  payment_id bigint not null,
  bill_id bigint not null,
  allocation_id bigint not null,
  amount decimal(14,2) not null,
  reason varchar(500),
  refund_status varchar(32) not null default 'SUCCESS',
  refunded_time datetime,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  unique key uk_refund_no (tenant_id,refund_no),
  key idx_refund_payment (tenant_id,payment_id),
  key idx_refund_bill (tenant_id,bill_id)
) engine=InnoDB default charset=utf8mb4 comment='账单退款';
