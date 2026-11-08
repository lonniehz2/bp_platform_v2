-- 场景菜单与角色模板种子
-- GUARANTEE 场景

insert ignore into bp_menu(id, scene_code, menu_code, parent_code, menu_name, menu_type, route, sort_no)
values
(920000000000000001,'GUARANTEE','dashboard',null,'工作台','MENU','/guarantee/dashboard',10),
(920000000000000002,'GUARANTEE','asset',null,'项目与资产','MENU','/guarantee/assets',20),
(920000000000000003,'GUARANTEE','person',null,'客户与人员','MENU','/guarantee/persons',30),
(920000000000000004,'GUARANTEE','application','person','申请管理','MENU','/guarantee/applications',31),
(920000000000000005,'GUARANTEE','waitlist','application','轮候配租','MENU','/guarantee/waitlist',32),
(920000000000000006,'GUARANTEE','contract',null,'合同与租赁','MENU','/guarantee/contracts',40),
(920000000000000007,'GUARANTEE','billing',null,'收费与账务','MENU','/guarantee/billing',50),
(920000000000000008,'GUARANTEE','deposit','billing','押金管理','MENU','/guarantee/deposits',51),
(920000000000000009,'GUARANTEE','subsidy','billing','补贴管理','MENU','/guarantee/subsidies',52),
(920000000000000010,'GUARANTEE','audit',null,'审核中心','MENU','/guarantee/audit',60),
(920000000000000011,'GUARANTEE','device',null,'设备与授权','MENU','/guarantee/devices',70),
(920000000000000012,'GUARANTEE','config',null,'基础配置','MENU','/guarantee/config',80),
(920000000000000013,'GUARANTEE','system',null,'系统与数据','MENU','/guarantee/system',90),
(920000000000000014,'GUARANTEE','service',null,'服务与工单','MENU','/guarantee/work-orders',65),
(920000000000000015,'GUARANTEE','access',null,'访客通行','MENU','/guarantee/access-records',75);

insert ignore into bp_role(id, tenant_id, scene_code, role_code, role_name, role_status)
values
(930000000000000001,'350600','GUARANTEE','GUARANTEE_ADMIN','保障房管理员','ENABLED'),
(930000000000000002,'350600','GUARANTEE','GUARANTEE_MANAGER','保障房经理','ENABLED'),
(930000000000000003,'350600','GUARANTEE','GUARANTEE_FINANCE','保障房财务','ENABLED'),
(930000000000000004,'350600','GUARANTEE','GUARANTEE_STEWARD','保障房客服','ENABLED');

-- 管理员全部菜单
insert ignore into bp_role_menu(id, tenant_id, role_id, menu_id)
select 940000000000000000 + row_number() over (order by id), '350600', 930000000000000001, id
from bp_menu where scene_code='GUARANTEE';

-- 经理：除系统配置外
insert ignore into bp_role_menu(id, tenant_id, role_id, menu_id)
select 940000000000100000 + row_number() over (order by id), '350600', 930000000000000002, id
from bp_menu where scene_code='GUARANTEE' and menu_code not in ('system');

-- 财务
insert ignore into bp_role_menu(id, tenant_id, role_id, menu_id)
select 940000000000200000 + row_number() over (order by id), '350600', 930000000000000003, id
from bp_menu where scene_code='GUARANTEE' and menu_code in ('dashboard','contract','billing','deposit','subsidy','audit');

-- 客服
insert ignore into bp_role_menu(id, tenant_id, role_id, menu_id)
select 940000000000300000 + row_number() over (order by id), '350600', 930000000000000004, id
from bp_menu where scene_code='GUARANTEE' and menu_code in ('dashboard','person','application','waitlist','contract','audit','device');
