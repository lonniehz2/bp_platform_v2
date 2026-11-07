-- 智慧物业 V1 分类管理基础表
-- 说明：分类为租户级；系统分类由平台预置，租户只能在允许扩展的父级下新增叶子分类。

create table if not exists prop_category (
  id bigint not null primary key,
  tenant_id varchar(32) not null,
  category_type varchar(20) not null comment 'INCOME/EXPENSE',
  parent_id bigint null,
  category_code varchar(64) not null,
  category_name varchar(128) not null,
  category_level int not null default 1,
  is_system tinyint not null default 0,
  is_leaf tinyint not null default 0,
  allow_custom tinyint not null default 0,
  report_line_code varchar(64) null,
  status varchar(20) not null default 'ENABLED',
  sort_no int not null default 0,
  remark varchar(500) null,
  is_deleted tinyint not null default 0,
  create_by varchar(64) null,
  create_time datetime not null default current_timestamp,
  update_by varchar(64) null,
  update_time datetime not null default current_timestamp on update current_timestamp,
  unique key uk_category_code (tenant_id, category_type, category_code),
  key idx_category_parent (tenant_id, category_type, parent_id),
  key idx_category_status (tenant_id, category_type, status)
) engine=InnoDB default charset=utf8mb4 comment='收入/支出分类';

-- 收入一级分类
insert ignore into prop_category
(id, tenant_id, category_type, parent_id, category_code, category_name, category_level,
 is_system, is_leaf, allow_custom, report_line_code, status, sort_no)
values
(377000000000000001, '350600', 'INCOME', null, 'PROPERTY_FEE', '物业费收入', 1, 1, 0, 1, 'PROPERTY_FEE', 'ENABLED', 10),
(377000000000000002, '350600', 'INCOME', null, 'PARKING', '停车收入', 1, 1, 0, 1, 'PARKING', 'ENABLED', 20),
(377000000000000003, '350600', 'INCOME', null, 'ENERGY', '能耗费收入', 1, 1, 0, 1, 'ENERGY', 'ENABLED', 30),
(377000000000000004, '350600', 'INCOME', null, 'LEASE', '租赁收入', 1, 1, 0, 1, 'LEASE', 'ENABLED', 40),
(377000000000000005, '350600', 'INCOME', null, 'MULTI_BUSINESS', '多经收入', 1, 1, 0, 1, 'MULTI_BUSINESS', 'ENABLED', 50),
(377000000000000006, '350600', 'INCOME', null, 'OTHER', '其他收入', 1, 1, 0, 1, 'OTHER', 'ENABLED', 60);

-- 收入二级分类
insert ignore into prop_category
(id, tenant_id, category_type, parent_id, category_code, category_name, category_level,
 is_system, is_leaf, allow_custom, report_line_code, status, sort_no)
values
(377000000000000101, '350600', 'INCOME', 377000000000000001, 'PROPERTY_FEE_RESIDENTIAL', '住宅物业费', 2, 1, 1, 0, 'PROPERTY_FEE', 'ENABLED', 10),
(377000000000000102, '350600', 'INCOME', 377000000000000001, 'PROPERTY_FEE_COMMERCIAL', '商业物业费', 2, 1, 1, 0, 'PROPERTY_FEE', 'ENABLED', 20),
(377000000000000111, '350600', 'INCOME', 377000000000000002, 'PARKING_MANAGEMENT', '车位管理费', 2, 1, 1, 0, 'PARKING', 'ENABLED', 10),
(377000000000000112, '350600', 'INCOME', 377000000000000002, 'PARKING_RENT', '车位租赁费', 2, 1, 1, 0, 'PARKING', 'ENABLED', 20),
(377000000000000113, '350600', 'INCOME', 377000000000000002, 'PARKING_TEMP', '临时停车费', 2, 1, 1, 0, 'PARKING', 'ENABLED', 30),
(377000000000000121, '350600', 'INCOME', 377000000000000003, 'ENERGY_WATER', '水费', 2, 1, 1, 0, 'ENERGY', 'ENABLED', 10),
(377000000000000122, '350600', 'INCOME', 377000000000000003, 'ENERGY_ELECTRICITY', '电费', 2, 1, 1, 0, 'ENERGY', 'ENABLED', 20),
(377000000000000123, '350600', 'INCOME', 377000000000000003, 'ENERGY_SHARE', '公共能耗分摊', 2, 1, 1, 0, 'ENERGY', 'ENABLED', 30),
(377000000000000131, '350600', 'INCOME', 377000000000000004, 'LEASE_SHOP', '商铺租金', 2, 1, 1, 0, 'LEASE', 'ENABLED', 10),
(377000000000000132, '350600', 'INCOME', 377000000000000004, 'LEASE_PUBLIC_ROOM', '公共用房租金', 2, 1, 1, 0, 'LEASE', 'ENABLED', 20),
(377000000000000133, '350600', 'INCOME', 377000000000000004, 'LEASE_VENUE', '场地租赁', 2, 1, 1, 0, 'LEASE', 'ENABLED', 30),
(377000000000000141, '350600', 'INCOME', 377000000000000005, 'MULTI_ADVERTISING', '广告位收入', 2, 1, 1, 0, 'MULTI_BUSINESS', 'ENABLED', 10),
(377000000000000142, '350600', 'INCOME', 377000000000000005, 'MULTI_PUBLIC_AREA', '公共区域经营', 2, 1, 1, 0, 'MULTI_BUSINESS', 'ENABLED', 20),
(377000000000000143, '350600', 'INCOME', 377000000000000005, 'MULTI_TEMP_VENUE', '临时场地租赁', 2, 1, 1, 0, 'MULTI_BUSINESS', 'ENABLED', 30),
(377000000000000144, '350600', 'INCOME', 377000000000000005, 'MULTI_VALUE_ADDED', '增值服务', 2, 1, 1, 0, 'MULTI_BUSINESS', 'ENABLED', 40),
(377000000000000145, '350600', 'INCOME', 377000000000000005, 'MULTI_COOPERATION', '合作经营', 2, 1, 1, 0, 'MULTI_BUSINESS', 'ENABLED', 50),
(377000000000000146, '350600', 'INCOME', 377000000000000005, 'MULTI_OTHER', '其他多经收入', 2, 1, 1, 0, 'MULTI_BUSINESS', 'ENABLED', 60),
(377000000000000151, '350600', 'INCOME', 377000000000000006, 'OTHER_INCOME', '其他收入', 2, 1, 1, 0, 'OTHER', 'ENABLED', 10);

-- 支出一级分类
insert ignore into prop_category
(id, tenant_id, category_type, parent_id, category_code, category_name, category_level,
 is_system, is_leaf, allow_custom, report_line_code, status, sort_no)
values
(377000000000001001, '350600', 'EXPENSE', null, 'LABOR', '人力成本', 1, 1, 0, 1, 'LABOR', 'ENABLED', 10),
(377000000000001002, '350600', 'EXPENSE', null, 'OFFICE', '办公费用', 1, 1, 0, 1, 'OFFICE', 'ENABLED', 20),
(377000000000001003, '350600', 'EXPENSE', null, 'ENGINEERING', '工程维护', 1, 1, 0, 1, 'ENGINEERING', 'ENABLED', 30),
(377000000000001004, '350600', 'EXPENSE', null, 'MANAGEMENT', '管理费用', 1, 1, 0, 1, 'MANAGEMENT', 'ENABLED', 40),
(377000000000001005, '350600', 'EXPENSE', null, 'FINANCE', '财务费用', 1, 1, 0, 1, 'FINANCE', 'ENABLED', 50),
(377000000000001006, '350600', 'EXPENSE', null, 'TAX', '税费', 1, 1, 0, 1, 'TAX', 'ENABLED', 60),
(377000000000001007, '350600', 'EXPENSE', null, 'DEPRECIATION', '资产折旧', 1, 1, 0, 1, 'DEPRECIATION', 'ENABLED', 70),
(377000000000001008, '350600', 'EXPENSE', null, 'OTHER', '其他支出', 1, 1, 0, 1, 'OTHER', 'ENABLED', 80);

-- 支出二级分类
insert ignore into prop_category
(id, tenant_id, category_type, parent_id, category_code, category_name, category_level,
 is_system, is_leaf, allow_custom, report_line_code, status, sort_no)
values
(377000000000001101, '350600', 'EXPENSE', 377000000000001001, 'LABOR_SALARY', '工资', 2, 1, 1, 0, 'LABOR', 'ENABLED', 10),
(377000000000001102, '350600', 'EXPENSE', 377000000000001001, 'LABOR_SOCIAL', '社保', 2, 1, 1, 0, 'LABOR', 'ENABLED', 20),
(377000000000001103, '350600', 'EXPENSE', 377000000000001001, 'LABOR_WELFARE', '福利', 2, 1, 1, 0, 'LABOR', 'ENABLED', 30),
(377000000000001104, '350600', 'EXPENSE', 377000000000001001, 'LABOR_MEAL', '餐费', 2, 1, 1, 0, 'LABOR', 'ENABLED', 40),
(377000000000001111, '350600', 'EXPENSE', 377000000000001002, 'OFFICE_OFFICE', '办公费', 2, 1, 1, 0, 'OFFICE', 'ENABLED', 10),
(377000000000001112, '350600', 'EXPENSE', 377000000000001002, 'OFFICE_COMMUNICATION', '通讯费', 2, 1, 1, 0, 'OFFICE', 'ENABLED', 20),
(377000000000001113, '350600', 'EXPENSE', 377000000000001002, 'OFFICE_ENTERTAIN', '招待费', 2, 1, 1, 0, 'OFFICE', 'ENABLED', 30),
(377000000000001114, '350600', 'EXPENSE', 377000000000001002, 'OFFICE_BUSINESS', '商务费', 2, 1, 1, 0, 'OFFICE', 'ENABLED', 40),
(377000000000001121, '350600', 'EXPENSE', 377000000000001003, 'ENG_ELEVATOR_MAINT', '电梯维保', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 10),
(377000000000001122, '350600', 'EXPENSE', 377000000000001003, 'ENG_ELEVATOR_INSPECT', '电梯年检', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 20),
(377000000000001123, '350600', 'EXPENSE', 377000000000001003, 'ENG_ELEVATOR_REPAIR', '电梯维修', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 30),
(377000000000001124, '350600', 'EXPENSE', 377000000000001003, 'ENG_FIRE_MAINT', '消防维保', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 40),
(377000000000001125, '350600', 'EXPENSE', 377000000000001003, 'ENG_FIRE_REPAIR', '消防维修', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 50),
(377000000000001126, '350600', 'EXPENSE', 377000000000001003, 'ENG_WEAK_MAINT', '弱电维护', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 60),
(377000000000001127, '350600', 'EXPENSE', 377000000000001003, 'ENG_WEAK_REPAIR', '弱电维修', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 70),
(377000000000001128, '350600', 'EXPENSE', 377000000000001003, 'ENG_GARBAGE', '垃圾清运', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 80),
(377000000000001129, '350600', 'EXPENSE', 377000000000001003, 'ENG_EQUIPMENT_REPAIR', '设备维修', 2, 1, 1, 0, 'ENGINEERING', 'ENABLED', 90);
