-- 智慧物业 V1 业务平台 Schema 草案
-- 说明：本文件为设计评审稿，未执行；上线前需评审字段、索引和迁移顺序。
-- 平台化待评审：审批表是否改为 bp_wf_*，供应商是否改为 bp_supplier，优惠是否改为 bp_discount_*。
-- 数据库：MySQL 8
-- 编码：utf8mb4

-- =========================================================
-- 1. 空间结构模板（平台资产基础配置，租户级，场景共用）
-- =========================================================
create table if not exists bp_asset_space_template (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  template_code varchar(64) not null,
  template_name varchar(128) not null,
  scene_code varchar(32) not null,
  asset_type_code varchar(64) null,
  level_count int not null,
  levels_json json not null,
  is_system tinyint not null default 0,
  version_no int not null default 1,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_space_template_code (tenant_id, template_code, version_no),
  key idx_bp_space_template_scene (tenant_id, scene_code, status),
  key idx_bp_space_template_type (tenant_id, asset_type_code, status)
) engine=InnoDB default charset=utf8mb4 comment='空间结构模板，平台资产基础配置，租户级；物业/保障房/园区等场景共用';

-- =========================================================
-- 2. 资产类型字典（平台资产基础配置，租户级，多场景共用）
-- =========================================================
create table if not exists bp_asset_type (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  type_code varchar(64) not null,
  type_name varchar(128) not null,
  scene_code varchar(32) not null,
  type_category varchar(20) not null,
  sort_no int not null default 0,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_bp_asset_type_code (tenant_id, scene_code, type_code),
  key idx_bp_asset_type_category (tenant_id, scene_code, type_category, status)
) engine=InnoDB default charset=utf8mb4 comment='资产类型字典，平台资产基础配置，租户级；多场景共用';

-- =========================================================
-- 3. 物业房屋扩展
-- =========================================================
create table if not exists prop_unit_ext (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint not null,
  asset_type_code varchar(64) null,
  building_area decimal(14,2) null,
  inner_area decimal(14,2) null,
  property_type varchar(32) null,
  delivery_status varchar(20) null,
  delivery_date date null,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_unit_ext_house (tenant_id, house_id),
  key idx_prop_unit_ext_project (tenant_id, project_id, asset_type_code)
) engine=InnoDB default charset=utf8mb4 comment='物业房屋扩展';

-- =========================================================
-- 4. 物业服务合同（项目级整体合同）
-- =========================================================
create table if not exists prop_service_contract (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_no varchar(64) not null,
  contract_name varchar(200) not null,
  party_type varchar(32) not null,
  party_name varchar(200) not null,
  start_date date not null,
  end_date date not null,
  scope_type varchar(20) not null default 'PROJECT',
  scope_id bigint null,
  scope_desc varchar(500) null,
  system_flag tinyint not null default 0,
  contract_status varchar(20) not null default 'ACTIVE',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_service_contract_no (tenant_id, contract_no),
  key idx_prop_service_contract_project (tenant_id, project_id, contract_status)
) engine=InnoDB default charset=utf8mb4 comment='物业服务合同，项目级整体合同';

-- =========================================================
-- 5. 计费方案
-- =========================================================
create table if not exists prop_billing_scheme (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  scheme_name varchar(200) not null,
  fee_item_id bigint not null,
  fee_category varchar(32) not null,
  asset_type_code varchar(64) null,
  scope_type varchar(20) not null,
  scope_id bigint null,
  unit_price decimal(14,4) not null default 0,
  billing_cycle varchar(20) not null default 'MONTH',
  start_date date not null,
  end_date date null,
  auto_generate tinyint not null default 1,
  scheme_status varchar(20) not null default 'ENABLED',
  version_no int not null default 1,
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_scheme_project (tenant_id, project_id, scheme_status),
  key idx_prop_scheme_scope (tenant_id, project_id, scope_type, scope_id),
  key idx_prop_scheme_asset_type (tenant_id, project_id, asset_type_code, fee_item_id)
) engine=InnoDB default charset=utf8mb4 comment='计费方案，按项目/资产类型/楼栋/房屋';

-- =========================================================
-- 6. 合同与计费方案关系（物业服务合同/租赁合同均可关联）
-- =========================================================
create table if not exists prop_contract_scheme (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  contract_type varchar(20) not null,
  contract_id bigint not null,
  scheme_id bigint not null,
  effective_from date not null,
  effective_to date null,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_contract_scheme (tenant_id, contract_type, contract_id, scheme_id, effective_from),
  key idx_prop_contract_scheme_contract (tenant_id, contract_type, contract_id, status)
) engine=InnoDB default charset=utf8mb4 comment='合同与计费方案关系';

-- =========================================================
-- 7. 审核流程配置
-- =========================================================
create table if not exists prop_audit_flow (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint null,
  biz_type varchar(32) not null,
  flow_name varchar(128) not null,
  amount_min decimal(14,2) null,
  amount_max decimal(14,2) null,
  priority_no int not null default 0,
  flow_status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_audit_flow_biz (tenant_id, project_id, biz_type, flow_status)
) engine=InnoDB default charset=utf8mb4 comment='审核流程配置';

create table if not exists prop_audit_node (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  flow_id bigint not null,
  node_seq int not null,
  node_name varchar(128) not null,
  approve_mode varchar(20) not null default 'SERIAL',
  approve_rule varchar(20) not null default 'ALL',
  approver_type varchar(20) not null default 'ROLE',
  approver_value varchar(500) not null,
  node_status varchar(20) not null default 'ENABLED',
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_audit_node_seq (tenant_id, flow_id, node_seq),
  key idx_prop_audit_node_flow (tenant_id, flow_id, node_status)
) engine=InnoDB default charset=utf8mb4 comment='审核节点配置';

create table if not exists prop_audit_task (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint null,
  biz_type varchar(32) not null,
  biz_id bigint not null,
  flow_id bigint not null,
  current_node_id bigint null,
  task_status varchar(20) not null default 'PENDING',
  submitter_id bigint null,
  submitter_name varchar(128) null,
  amount decimal(14,2) null,
  summary varchar(1000) null,
  submit_time datetime not null default current_timestamp,
  finish_time datetime null,
  is_deleted tinyint not null default 0,
  create_time datetime not null default current_timestamp,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_audit_task_biz (tenant_id, biz_type, biz_id),
  key idx_prop_audit_task_status (tenant_id, project_id, task_status)
) engine=InnoDB default charset=utf8mb4 comment='审核任务';

create table if not exists prop_audit_record (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  task_id bigint not null,
  node_id bigint null,
  approver_id bigint null,
  approver_name varchar(128) null,
  action varchar(20) not null,
  comment_text varchar(1000) null,
  action_time datetime not null default current_timestamp,
  key idx_prop_audit_record_task (tenant_id, task_id, action_time)
) engine=InnoDB default charset=utf8mb4 comment='审核记录';

-- =========================================================
-- 8. 人员组
-- =========================================================
create table if not exists prop_person_group (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  group_code varchar(64) not null,
  group_name varchar(128) not null,
  group_type varchar(20) not null,
  status varchar(20) not null default 'ENABLED',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_person_group_code (tenant_id, project_id, group_code),
  key idx_prop_person_group_project (tenant_id, project_id, group_type, status)
) engine=InnoDB default charset=utf8mb4 comment='人员组';

create table if not exists prop_person_group_member (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  group_id bigint not null,
  person_id bigint not null,
  joined_time datetime not null default current_timestamp,
  unique key uk_prop_person_group_member (tenant_id, group_id, person_id),
  key idx_prop_person_group_member_person (tenant_id, person_id)
) engine=InnoDB default charset=utf8mb4 comment='人员组成员';

-- =========================================================
-- 9. 供应商与服务人员
-- =========================================================
create table if not exists prop_supplier (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint null,
  supplier_code varchar(64) not null,
  supplier_name varchar(200) not null,
  service_category varchar(64) null,
  contact_name varchar(128) null,
  contact_phone varchar(32) null,
  status varchar(20) not null default 'ENABLED',
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_prop_supplier_code (tenant_id, supplier_code),
  key idx_prop_supplier_project (tenant_id, project_id, status)
) engine=InnoDB default charset=utf8mb4 comment='供应商';

create table if not exists prop_service_staff (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint null,
  supplier_id bigint null,
  person_id bigint null,
  staff_name varchar(128) not null,
  phone varchar(32) null,
  skill_type varchar(64) null,
  status varchar(20) not null default 'ENABLED',
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_service_staff_supplier (tenant_id, supplier_id, status),
  key idx_prop_service_staff_person (tenant_id, person_id)
) engine=InnoDB default charset=utf8mb4 comment='服务人员';

-- =========================================================
-- 10. 资产异常
-- =========================================================
create table if not exists prop_asset_exception (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  project_id bigint not null,
  house_id bigint null,
  space_id bigint null,
  exception_type varchar(32) not null,
  exception_desc varchar(1000) null,
  exception_status varchar(20) not null default 'PENDING',
  handle_user_id bigint null,
  handle_time datetime null,
  handle_result varchar(1000) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  key idx_prop_asset_exception_project (tenant_id, project_id, exception_status),
  key idx_prop_asset_exception_house (tenant_id, house_id)
) engine=InnoDB default charset=utf8mb4 comment='资产异常';

-- =========================================================
-- 11. 已有表增量字段（草案，评审后再执行）
-- =========================================================
-- alter table bp_iam_org add column space_template_id bigint null comment '空间结构模板，平台资产基础配置';
-- alter table bp_iam_org add column default_asset_type_code varchar(64) null comment '默认资产类型';
-- alter table bp_asset_space add column asset_type_code varchar(64) null comment '资产类型';
-- alter table bp_asset_space add column space_template_id bigint null comment '空间结构模板';
-- alter table bp_asset_space add column level_no int null comment '所在层级序号';
-- alter table bp_person add column face_photo_url varchar(500) null comment '人脸照片，非必填';
-- alter table prop_fee_item add column fee_category varchar(32) null comment '收费项目类别';
-- alter table prop_bill add column contract_type varchar(20) null comment '合同类型';
-- alter table prop_bill add column scheme_id bigint null comment '计费方案';
-- alter table prop_bill add column asset_type_code varchar(64) null comment '资产类型快照';

-- =========================================================
-- 12. 建议种子数据
-- =========================================================
-- 资产类型
-- RES_HIGH_RISE 高层住宅
-- RES_MULTI 多层住宅
-- RES_TOWNHOUSE 排屋/别墅
-- COMMERCIAL 商业
-- SHOP 商铺
-- OFFICE 办公
-- WAREHOUSE 仓库
-- PARKING_GARAGE 车库车位
-- PARKING_OPEN 露天车位
-- PARKING_UNDERGROUND 地下车位
-- PARKING_EV 充电车位

-- 收费项目类别
-- PROPERTY_FEE 物业费
-- ENERGY 能耗费
-- WATER 水费
-- ELECTRICITY 电费
-- PARKING_MGMT 车位管理费
-- RENT 租金
-- OTHER 其他

-- 空间模板（bp_asset_space_template，scene_code 区分场景）
-- 物业住宅：期/苑幢/单元/楼层/房号
-- 物业商业：楼/楼层/商铺
-- 物业办公：楼/楼层/房间
-- 物业场地：区域/点位
-- 保障房：小区/楼栋/单元/楼层/房屋/床位
-- 园区：园区/楼栋/楼层/房间
-- 校园：校区/楼栋/楼层/房间
