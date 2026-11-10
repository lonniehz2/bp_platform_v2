-- 本地 Docker 演示数据：一套完整业务闭环
-- 统一前缀 DEMO，固定 ID 990，验证脚本不会冲突

-- 项目
insert ignore into bp_org
(id, tenant_id, parent_id, org_code, org_name, org_type, scene_code, business_mode, space_template_id,
 default_asset_type_code, address, contact_name, contact_phone, total_area, org_path, sort_no, status, is_deleted)
values
(990000000000000001,'350600',null,'DEMO_PROJECT','演示保障房项目','PROJECT','GUARANTEE','PUBLIC_RENTAL',
 910000000000003001,'PUBLIC_RENTAL','演示市演示路 1 号','演示管理员','13800000000',12000.00,'DEMO_PROJECT',1,'ENABLED',0);

-- 空间
insert ignore into bp_space
(id, tenant_id, org_id, parent_id, space_code, space_name, space_type, space_path, level_no, asset_type_code,
 space_template_id, business_mode, sub_unit_mode, area, sort_no, status, is_deleted)
values
(990000000000000101,'350600',990000000000000001,null,'DEMO_BUILDING','1 号楼','BUILDING','1 号楼',1,'PUBLIC_RENTAL',910000000000003001,'PUBLIC_RENTAL',null,6000.00,1,'ENABLED',0),
(990000000000000102,'350600',990000000000000001,990000000000000101,'DEMO_UNIT_1','1 单元','UNIT','1 号楼 / 1 单元',2,'PUBLIC_RENTAL',910000000000003001,'PUBLIC_RENTAL',null,3000.00,2,'ENABLED',0),
(990000000000000103,'350600',990000000000000001,990000000000000102,'DEMO_ROOM_101','101 室','ROOM','1 号楼 / 1 单元 / 101 室',3,'PUBLIC_RENTAL',910000000000003001,'PUBLIC_RENTAL',null,80.00,3,'ENABLED',0),
(990000000000000104,'350600',990000000000000001,990000000000000102,'DEMO_ROOM_102','102 室','ROOM','1 号楼 / 1 单元 / 102 室',3,'PUBLIC_RENTAL',910000000000003001,'PUBLIC_RENTAL',null,75.00,4,'ENABLED',0),
(990000000000000105,'350600',990000000000000001,990000000000000101,'DEMO_ROOM_201','201 室','ROOM','1 号楼 / 201 室',2,'PUBLIC_RENTAL',910000000000003001,'PUBLIC_RENTAL',null,90.00,5,'ENABLED',0);

-- 房屋
insert ignore into bp_house
(id, tenant_id, org_id, space_id, house_code, house_name, asset_type_code, area, inner_area, house_status,
 layout_type, orientation, floor_no, total_floors, is_deleted)
values
(990000000000000201,'350600',990000000000000001,990000000000000103,'DEMO_HOUSE_101','1-101','PUBLIC_RENTAL',80.00,68.00,'RENTED','TWO_BED','SOUTH',1,18,0),
(990000000000000202,'350600',990000000000000001,990000000000000104,'DEMO_HOUSE_102','1-102','PUBLIC_RENTAL',75.00,63.00,'VACANT','ONE_BED','SOUTH',1,18,0),
(990000000000000203,'350600',990000000000000001,990000000000000105,'DEMO_HOUSE_201','1-201','PUBLIC_RENTAL',90.00,76.00,'RENTED','TWO_BED','SOUTH',2,18,0);

-- 人员
insert ignore into bp_person
(id, tenant_id, org_id, person_code, person_name, phone, id_card_mask, person_type, gender, birth_date,
 address, employer, emergency_contact, remark, verify_status, status, is_deleted)
values
(990000000000000301,'350600',990000000000000001,'DEMO_P_001','演示承租人张三','13800000001','3301**********1234','GUARANTEE_TENANT','MALE','1988-05-12','演示市演示路 1 号','演示科技有限公司','李四 13900000001','演示主承租人','VERIFIED','ENABLED',0),
(990000000000000302,'350600',990000000000000001,'DEMO_P_002','演示同住人李四','13800000002','3301**********5678','COHABITANT','FEMALE','1990-08-20','演示市演示路 1 号','演示医院','张三 13900000000','配偶','VERIFIED','ENABLED',0),
(990000000000000303,'350600',990000000000000001,'DEMO_P_003','演示同住人小明','13800000003','3301**********9012','COHABITANT','MALE','2015-03-01','演示市演示路 1 号','演示小学','张三 13900000000','子女','VERIFIED','ENABLED',0),
(990000000000000304,'350600',990000000000000001,'DEMO_P_004','演示承租人王五','13800000004','3301**********3456','GUARANTEE_TENANT','MALE','1985-11-02','演示市演示路 2 号','演示物流','赵六 13900000004','另一合同承租人','VERIFIED','ENABLED',0),
(990000000000000305,'350600',990000000000000001,'DEMO_P_005','演示同住人赵六','13800000005','3301**********7890','COHABITANT','FEMALE','1987-02-14','演示市演示路 2 号','演示超市','王五 13900000004','同住人','VERIFIED','ENABLED',0);

-- 申请
insert ignore into guarantee_application
(id, tenant_id, project_id, application_no, applicant_person_id, application_type, family_size, contact_phone,
 income_level, housing_status, urgency, remark, guarantee_type, family_type, subsidy_status, archive_no,
 application_status, submit_time, review_time, review_comment, is_deleted)
values
(990000000000000401,'350600',990000000000000001,'DEMO_APP_001',990000000000000301,'PUBLIC_RENTAL',3,'13800000001','LOW','NO_HOUSE','NORMAL','演示申请','PUBLIC_RENTAL','FAMILY','NORMAL','DEMO_ARCHIVE_001','APPROVED',now(),now(),'审核通过',0);

-- 轮候
insert ignore into guarantee_waitlist
(id, tenant_id, project_id, application_id, queue_no, waitlist_status, joined_time, is_deleted)
values
(990000000000000501,'350600',990000000000000001,990000000000000401,'DEMO_Q_001','ALLOCATED',now(),0);

-- 配租
insert ignore into guarantee_allocation
(id, tenant_id, project_id, application_id, house_id, allocation_no, allocation_status, contract_id, allocated_time, is_deleted)
values
(990000000000000601,'350600',990000000000000001,990000000000000401,990000000000000201,'DEMO_AL_001','CONTRACTED',990000000000000701,now(),0);

-- 合同
insert ignore into guarantee_contract
(id, tenant_id, project_id, contract_no, house_id, person_id, start_date, end_date, rent_amount, deposit_amount,
 billing_cycle, bill_day, contract_status, remark, is_deleted)
values
(990000000000000701,'350600',990000000000000001,'DEMO_HT_001',990000000000000201,990000000000000301,'2026-01-01','2026-12-31',1200.00,1200.00,'MONTH',1,'ACTIVE','演示生效合同',0),
(990000000000000702,'350600',990000000000000001,'DEMO_HT_002',990000000000000203,990000000000000304,'2026-03-01','2027-02-28',1500.00,1500.00,'MONTH',5,'ACTIVE','演示第二份合同',0),
(990000000000000703,'350600',990000000000000001,'DEMO_HT_DRAFT',990000000000000202,990000000000000301,'2027-01-01','2027-12-31',900.00,900.00,'MONTH',1,'DRAFT','演示草稿合同',0);

-- 同住人
insert ignore into guarantee_contract_cohabitant
(id, tenant_id, contract_id, person_id, relation_type, is_primary, start_date, end_date, cohabitant_status, remark, is_deleted)
values
(990000000000000801,'350600',990000000000000701,990000000000000302,'SPOUSE',1,'2026-01-01',null,'ACTIVE','配偶',0),
(990000000000000802,'350600',990000000000000701,990000000000000303,'CHILD',0,'2026-01-01',null,'ACTIVE','子女',0),
(990000000000000803,'350600',990000000000000702,990000000000000305,'SPOUSE',1,'2026-03-01',null,'ACTIVE','配偶',0);

-- 押金
insert ignore into guarantee_deposit
(id, tenant_id, project_id, contract_id, person_id, amount, paid_amount, refunded_amount, deposit_status, is_deleted)
values
(990000000000000901,'350600',990000000000000001,990000000000000701,990000000000000301,1200.00,1200.00,0.00,'PAID',0),
(990000000000000902,'350600',990000000000000001,990000000000000702,990000000000000304,1500.00,1500.00,0.00,'PAID',0);

-- 账单
insert ignore into bp_bill
(id, tenant_id, project_id, bill_no, biz_type, contract_type, contract_id, house_id, person_id,
 fee_item_code, period_start, period_end, amount, discount_amount, payable_amount, paid_amount,
 bill_status, due_date, source_type, source_id, remark, is_deleted)
values
(990000000000001001,'350600',990000000000000001,'DEMO_BILL_001','RENT','GUARANTEE',990000000000000701,990000000000000201,990000000000000301,'RENT','2026-01-01','2026-01-31',1200.00,0,1200.00,1200.00,'PAID','2026-01-10','CONTRACT',990000000000000701,'演示已收租金',0),
(990000000000001002,'350600',990000000000000001,'DEMO_BILL_002','RENT','GUARANTEE',990000000000000701,990000000000000201,990000000000000301,'RENT','2026-02-01','2026-02-28',1200.00,0,1200.00,0.00,'UNPAID','2026-02-10','CONTRACT',990000000000000701,'演示未收租金',0),
(990000000000001003,'350600',990000000000000001,'DEMO_BILL_003','RENT','GUARANTEE',990000000000000702,990000000000000203,990000000000000304,'RENT','2026-03-01','2026-03-31',1500.00,0,1500.00,0.00,'UNPAID','2026-03-10','CONTRACT',990000000000000702,'演示第二合同租金',0),
(990000000000001004,'350600',990000000000000001,'DEMO_BILL_004','WATER','GUARANTEE',990000000000000701,990000000000000201,990000000000000301,'WATER','2026-04-01','2026-04-30',35.00,0,35.00,0.00,'UNPAID','2026-04-30','METER',990000000000002201,'演示水费',0);

-- 收款
insert ignore into bp_payment
(id, tenant_id, project_id, payment_no, payer_person_id, amount, payment_method, payment_status, paid_time, remark, is_deleted)
values
(990000000000001101,'350600',990000000000000001,'DEMO_PAY_001',990000000000000301,1200.00,'CASH','SUCCESS','2026-01-05 10:00:00','演示收款',0);
insert ignore into bp_payment_allocation(id, tenant_id, payment_id, bill_id, amount)
values (990000000000001201,'350600',990000000000001101,990000000000001001,1200.00);

-- 补贴
insert ignore into guarantee_subsidy
(id, tenant_id, project_id, contract_id, subsidy_type, subsidy_amount, start_date, end_date, subsidy_status, remark, is_deleted)
values
(990000000000001301,'350600',990000000000000001,990000000000000701,'RENT_SUBSIDY',300.00,'2026-01-01','2026-12-31','ACTIVE','演示租金补贴',0);

-- 设备
insert ignore into bp_dev_device
(id, tenant_id, project_id, space_id, device_code, device_name, device_type, device_model, asset_status,
 business_status, install_time, warranty_end, remark, device_mac, is_virtual, install_status, is_deleted)
values
(990000000000001401,'350600',990000000000000001,990000000000000103,'DEMO_DEV_LOCK_101','101 智能门锁','INDOOR_LOCK','DEMO-LOCK', 'ACTIVE','IN_USE','2026-01-01', '2028-01-01','演示门锁','AA:BB:CC:DD:EE:01',0,'INSTALLED',0),
(990000000000001402,'350600',990000000000000001,990000000000000101,'DEMO_DEV_GATE','园区通道闸','PASSAGE','DEMO-GATE','ACTIVE','IN_USE','2026-01-01','2028-01-01','演示通道闸','AA:BB:CC:DD:EE:02',0,'INSTALLED',0);

-- 授权
insert ignore into bp_grant_entitlement
(id, tenant_id, project_id, person_id, target_type, target_id, grant_level, valid_start, valid_end,
 grant_status, source_type, source_id, revoke_reason, is_deleted)
values
(990000000000001501,'350600',990000000000000001,990000000000000301,'DEVICE',990000000000001401,'OWNER','2026-01-01','2026-12-31','ACTIVE','CONTRACT',990000000000000701,null,0),
(990000000000001502,'350600',990000000000000001,990000000000000302,'DEVICE',990000000000001401,'MEMBER','2026-01-01','2026-12-31','ACTIVE','CONTRACT',990000000000000701,null,0),
(990000000000001503,'350600',990000000000000001,990000000000000301,'DEVICE',990000000000001402,'PASSAGE','2026-01-01','2026-12-31','ACTIVE','CONTRACT',990000000000000701,null,0);

-- 通行记录
insert ignore into guarantee_access_record
(id, tenant_id, project_id, house_id, person_id, visitor_name, visitor_phone, purpose, valid_start, valid_end,
 access_status, is_deleted)
values
(990000000000001601,'350600',990000000000000001,990000000000000201,990000000000000301,'张三','13800000001','回家','2026-02-01 08:00:00','2026-02-01 20:00:00','ALLOWED',0);

-- 工单
insert ignore into guarantee_work_order
(id, tenant_id, project_id, order_no, order_type, title, description, house_id, person_id, priority,
 order_status, assignee_name, finish_time, is_deleted)
values
(990000000000001701,'350600',990000000000000001,'DEMO_WO_001','REPAIR','厨房水龙头漏水','承租人报修厨房水龙头','990000000000000201','990000000000000301','HIGH','OPEN','维修班组',null,0);

-- 预警
insert ignore into guarantee_alert
(id, tenant_id, project_id, alert_type, alert_level, title, content, house_id, person_id, alert_status,
 handler_name, handle_result, is_deleted)
values
(990000000000001801,'350600',990000000000000001,'ARREARS','HIGH','演示欠费预警','合同 DEMO_HT_001 存在未收租金',990000000000000201,990000000000000301,'PENDING',null,null,0);

-- 投诉
insert ignore into guarantee_complaint
(id, tenant_id, project_id, complaint_type, title, content, house_id, person_id, complaint_status,
 handler_name, handle_result, is_deleted)
values
(990000000000001901,'350600',990000000000000001,'NOISE','夜间噪音投诉','楼上夜间噪音',990000000000000201,990000000000000301,'PROCESSING','客服组',null,0);

-- 公示
insert ignore into guarantee_publicity
(id, tenant_id, project_id, publicity_type, title, content, start_date, end_date, publicity_status, is_deleted)
values
(990000000000002001,'350600',990000000000000001,'ALLOCATION','2026 年第一批配租公示','演示配租结果公示','2026-01-01','2026-01-15','PUBLISHED',0);

-- 收费项目
insert ignore into guarantee_fee_item
(id, tenant_id, project_id, fee_code, fee_name, fee_type, billing_cycle, unit_price, unit_name, tax_rate,
 fee_status, is_deleted)
values
(990000000000002101,'350600',990000000000000001,'DEMO_RENT','演示租金','RENT','MONTH',1200.00,'元/月',0.00,'ENABLED',0),
(990000000000002102,'350600',990000000000000001,'DEMO_WATER','演示水费','UTILITY','MONTH',3.50,'元/吨',0.00,'ENABLED',0);

-- 仪表
insert ignore into guarantee_meter
(id, tenant_id, project_id, house_id, meter_type, meter_no, initial_reading, current_reading, install_date, meter_status, is_deleted)
values
(990000000000002201,'350600',990000000000000001,990000000000000201,'WATER','DEMO_METER_001',0,10,'2026-01-01','ACTIVE',0);
insert ignore into guarantee_meter_reading
(id, tenant_id, meter_id, reading_date, reading_value, previous_value, usage_amount, reader_name)
values
(990000000000002301,'350600',990000000000002201,'2026-02-01',10,0,10,'演示抄表员');

-- 房源展示/预约/订单
insert ignore into bp_listing
(id, tenant_id, project_id, house_id, title, description, monthly_rent, deposit_amount, listing_status, publish_time, cover_url, is_deleted)
values
(990000000000002401,'350600',990000000000000001,990000000000000202,'演示空置房源 1-102','两居室，交通便利',900.00,900.00,'PUBLISHED','2026-01-01 09:00:00',null,0);
insert ignore into bp_booking
(id, tenant_id, project_id, listing_id, person_id, booking_no, booking_status, contact_phone, remark, is_deleted)
values
(990000000000002501,'350600',990000000000000001,990000000000002401,990000000000000301,'DEMO_BOOK_001','PENDING','13800000001','演示看房预约',0);
insert ignore into bp_listing_order
(id, tenant_id, project_id, listing_id, booking_id, person_id, order_no, order_status, rent_amount, deposit_amount, is_deleted, payment_status)
values
(990000000000002601,'350600',990000000000000001,990000000000002401,990000000000002501,990000000000000301,'DEMO_ORDER_001','CONFIRMED',900.00,900.00,0,'UNPAID');

-- 合同变更
insert ignore into guarantee_contract_change
(id, tenant_id, project_id, contract_id, change_type, before_json, after_json, effective_date, change_status, reason, is_deleted)
values
(990000000000002701,'350600',990000000000000001,990000000000000701,'RENT_CHANGE',json_object('rentAmount',1200),json_object('rentAmount',1300),'2026-07-01','APPROVED','演示租金调整',0);

-- 资格复核
insert ignore into guarantee_qualification_review
(id, tenant_id, project_id, contract_id, person_id, review_type, review_year, review_status, review_date, reviewer_name, review_comment, next_review_date, is_deleted)
values
(990000000000002801,'350600',990000000000000001,990000000000000701,990000000000000301,'ANNUAL',2026,'PASSED','2026-03-01','演示审核员','演示复核通过','2027-03-01',0);

-- 演示账号（密码 admin123）
insert ignore into bp_user
(id, tenant_id, username, password_hash, display_name, user_status, is_deleted)
values
(990000000000002901,'350600','demo_manager','$2b$10$HVUYQSbuwXgAHW5uDfv1T.1ndyEO/8xhF5JSNEbe0dawi/dJinQl.','演示经理','ENABLED',0),
(990000000000002902,'350600','demo_finance','$2b$10$HVUYQSbuwXgAHW5uDfv1T.1ndyEO/8xhF5JSNEbe0dawi/dJinQl.','演示财务','ENABLED',0),
(990000000000002903,'350600','demo_steward','$2b$10$HVUYQSbuwXgAHW5uDfv1T.1ndyEO/8xhF5JSNEbe0dawi/dJinQl.','演示客服','ENABLED',0);
insert ignore into bp_user_role(id, tenant_id, user_id, role_id) values
(990000000000003001,'350600',990000000000002901,930000000000000002),
(990000000000003002,'350600',990000000000002902,930000000000000003),
(990000000000003003,'350600',990000000000002903,930000000000000004);
