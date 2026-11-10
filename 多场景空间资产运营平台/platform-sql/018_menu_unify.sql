-- 统一页面级菜单编码
-- 备份
create table if not exists bp_menu_bak_20261110 as select * from bp_menu;
create table if not exists bp_role_menu_bak_20261110 as select * from bp_role_menu;

START TRANSACTION;

-- 旧编码加前缀，避免与新页面编码冲突
update bp_menu set menu_code=concat('legacy_',menu_code) where scene_code='GUARANTEE';

-- 分组节点
insert ignore into bp_menu(id,scene_code,menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status) values
(921000000000000000,'GUARANTEE','group_workbench',null,'工作台','GROUP',null,10,'ENABLED'),
(921000000000000001,'GUARANTEE','group_application',null,'申请与资格','GROUP',null,20,'ENABLED'),
(921000000000000002,'GUARANTEE','group_waitlist',null,'轮候与配租','GROUP',null,30,'ENABLED'),
(921000000000000003,'GUARANTEE','group_contract',null,'合同与房源','GROUP',null,40,'ENABLED'),
(921000000000000004,'GUARANTEE','group_finance',null,'收费与账务','GROUP',null,50,'ENABLED'),
(921000000000000005,'GUARANTEE','group_asset',null,'房源与资产','GROUP',null,60,'ENABLED'),
(921000000000000006,'GUARANTEE','group_service',null,'服务与监督','GROUP',null,70,'ENABLED'),
(921000000000000007,'GUARANTEE','group_access',null,'通行与设备','GROUP',null,80,'ENABLED'),
(921000000000000008,'GUARANTEE','group_risk',null,'风险与预警','GROUP',null,90,'ENABLED'),
(921000000000000009,'GUARANTEE','group_system',null,'系统与数据','GROUP',null,100,'ENABLED');
-- 页面节点
insert ignore into bp_menu(id,scene_code,menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status) values
(922000000000000001,'GUARANTEE','dashboard','group_workbench','工作台','PAGE','/guarantee/dashboard',10,'ENABLED'),
(922000000000000002,'GUARANTEE','search','group_workbench','统一查询','PAGE','/guarantee/search',20,'ENABLED'),
(922000000000000003,'GUARANTEE','todos','group_workbench','我的待办','PAGE','/guarantee/todos',30,'ENABLED'),
(922000000000000004,'GUARANTEE','message','group_workbench','消息中心','PAGE','/guarantee/messages',40,'ENABLED'),
(922000000000000005,'GUARANTEE','applications','group_application','申请受理','PAGE','/guarantee/applications',50,'ENABLED'),
(922000000000000006,'GUARANTEE','person','group_application','人员档案','PAGE','/guarantee/persons',60,'ENABLED'),
(922000000000000007,'GUARANTEE','qualification','group_application','资格复核','PAGE','/guarantee/qualification',70,'ENABLED'),
(922000000000000008,'GUARANTEE','waitlist','group_waitlist','轮候管理','PAGE','/guarantee/waitlist',80,'ENABLED'),
(922000000000000009,'GUARANTEE','allocations','group_waitlist','配租摇号','PAGE','/guarantee/allocations',90,'ENABLED'),
(922000000000000010,'GUARANTEE','publicities','group_waitlist','公示管理','PAGE','/guarantee/publicities',100,'ENABLED'),
(922000000000000011,'GUARANTEE','contracts','group_contract','合同台账','PAGE','/guarantee/contracts',110,'ENABLED'),
(922000000000000012,'GUARANTEE','contractChanges','group_contract','合同变更','PAGE','/guarantee/contract-changes',120,'ENABLED'),
(922000000000000013,'GUARANTEE','exchanges','group_contract','换房管理','PAGE','/guarantee/exchanges',130,'ENABLED'),
(922000000000000014,'GUARANTEE','terminations','group_contract','退租管理','PAGE','/guarantee/terminations',140,'ENABLED'),
(922000000000000015,'GUARANTEE','billing','group_finance','账单与缴费','PAGE','/guarantee/billing',150,'ENABLED'),
(922000000000000016,'GUARANTEE','deposits','group_finance','押金管理','PAGE','/guarantee/deposits',160,'ENABLED'),
(922000000000000017,'GUARANTEE','subsidies','group_finance','补贴管理','PAGE','/guarantee/subsidies',170,'ENABLED'),
(922000000000000018,'GUARANTEE','cashflow','group_finance','资金流水','PAGE','/guarantee/cashflow',180,'ENABLED'),
(922000000000000019,'GUARANTEE','fee','group_finance','计费项目','PAGE','/guarantee/fee-items',190,'ENABLED'),
(922000000000000020,'GUARANTEE','arrears','group_finance','欠费清单','PAGE','/guarantee/arrears',200,'ENABLED'),
(922000000000000021,'GUARANTEE','asset','group_asset','项目与资产','PAGE','/guarantee/assets',210,'ENABLED'),
(922000000000000022,'GUARANTEE','listings','group_asset','房源展示','PAGE','/guarantee/listings',220,'ENABLED'),
(922000000000000023,'GUARANTEE','houses','group_asset','房源台账','PAGE','/guarantee/houses',230,'ENABLED'),
(922000000000000024,'GUARANTEE','spaces','group_asset','空间层级','PAGE','/guarantee/spaces',240,'ENABLED'),
(922000000000000025,'GUARANTEE','calendar','group_asset','日房态','PAGE','/guarantee/house-calendar',250,'ENABLED'),
(922000000000000026,'GUARANTEE','shortrent','group_asset','短租管理','PAGE','/guarantee/short-rent',260,'ENABLED'),
(922000000000000027,'GUARANTEE','workOrders','group_service','服务工单','PAGE','/guarantee/work-orders',270,'ENABLED'),
(922000000000000028,'GUARANTEE','complaints','group_service','投诉管理','PAGE','/guarantee/complaints',280,'ENABLED'),
(922000000000000029,'GUARANTEE','appeals','group_service','申诉管理','PAGE','/guarantee/appeals',290,'ENABLED'),
(922000000000000030,'GUARANTEE','visits','group_service','回访管理','PAGE','/guarantee/visits',300,'ENABLED'),
(922000000000000031,'GUARANTEE','devices','group_access','设备管理','PAGE','/guarantee/devices',310,'ENABLED'),
(922000000000000032,'GUARANTEE','deviceBind','group_access','设备绑定','PAGE','/guarantee/device-bind',320,'ENABLED'),
(922000000000000033,'GUARANTEE','devEvents','group_access','设备告警','PAGE','/guarantee/dev-events',330,'ENABLED'),
(922000000000000034,'GUARANTEE','accessRecords','group_access','通行记录','PAGE','/guarantee/access',340,'ENABLED'),
(922000000000000035,'GUARANTEE','keyring','group_access','钥匙包','PAGE','/guarantee/keyring',350,'ENABLED'),
(922000000000000036,'GUARANTEE','grants','group_access','通行授权','PAGE','/guarantee/grants',360,'ENABLED'),
(922000000000000037,'GUARANTEE','alertCenter','group_risk','预警中心','PAGE','/guarantee/alerts',370,'ENABLED'),
(922000000000000038,'GUARANTEE','patrol','group_risk','巡检管理','PAGE','/guarantee/patrol',380,'ENABLED'),
(922000000000000039,'GUARANTEE','houseAccess','group_risk','房源通行','PAGE','/guarantee/house-access',390,'ENABLED'),
(922000000000000040,'GUARANTEE','credit','group_risk','信用管理','PAGE','/guarantee/credits',400,'ENABLED'),
(922000000000000041,'GUARANTEE','audit','group_system','审批中心','PAGE','/guarantee/audit',410,'ENABLED'),
(922000000000000042,'GUARANTEE','reports','group_system','运营报表','PAGE','/guarantee/reports',420,'ENABLED'),
(922000000000000043,'GUARANTEE','gov','group_system','监管报送','PAGE','/guarantee/gov',430,'ENABLED'),
(922000000000000044,'GUARANTEE','orgs','group_system','组织机构','PAGE','/guarantee/orgs',440,'ENABLED'),
(922000000000000045,'GUARANTEE','rbac','group_system','用户与权限','PAGE','/guarantee/rbac',450,'ENABLED'),
(922000000000000046,'GUARANTEE','batchImport','group_system','批量导入','PAGE','/guarantee/imports',460,'ENABLED'),
(922000000000000047,'GUARANTEE','sys','group_system','系统支撑','PAGE','/guarantee/sys',470,'ENABLED'),
(922000000000000048,'GUARANTEE','help','group_system','使用帮助','PAGE','/guarantee/help',480,'ENABLED');
-- 旧编码到新页面映射
create temporary table tmp_menu_map(old_code varchar(64), new_code varchar(64)) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci;
insert into tmp_menu_map values
('legacy_dashboard','dashboard'),('legacy_search','search'),('legacy_message','message'),
('legacy_asset','asset'),('legacy_asset','listings'),('legacy_asset','houses'),('legacy_asset','spaces'),('legacy_asset','calendar'),('legacy_asset','shortrent'),
('legacy_person','person'),('legacy_person','keyring'),
('legacy_application','applications'),('legacy_application','allocations'),('legacy_application','qualification'),
('legacy_waitlist','waitlist'),
('legacy_contract','contracts'),('legacy_contract','contractChanges'),('legacy_contract','exchanges'),('legacy_contract','terminations'),
('legacy_billing','billing'),('legacy_billing','deposits'),('legacy_billing','subsidies'),('legacy_billing','cashflow'),('legacy_billing','fee'),('legacy_billing','arrears'),
('legacy_audit','audit'),('legacy_audit','todos'),
('legacy_service','workOrders'),
('legacy_device','devices'),('legacy_device','deviceBind'),('legacy_device','grants'),('legacy_device','houseAccess'),
('legacy_access','accessRecords'),
('legacy_complaint','complaints'),('legacy_complaint','appeals'),('legacy_complaint','visits'),
('legacy_publicity','publicities'),
('legacy_alert','alertCenter'),('legacy_alert','patrol'),('legacy_alert','devEvents'),
('legacy_credit','credit'),('legacy_shortrent','shortrent'),
('legacy_system','sys'),('legacy_system','rbac'),('legacy_system','batchImport'),('legacy_system','reports'),('legacy_system','orgs'),
('legacy_config','rbac'),('legacy_config','batchImport'),('legacy_config','sys'),
('legacy_calendar','calendar'),('legacy_energy','energy'),('legacy_gov','gov'),('legacy_help','help');
-- 旧角色授权迁移到页面
insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
select UUID_SHORT(),rm.tenant_id,rm.role_id,p.id
from bp_role_menu rm
join bp_menu old on old.id=rm.menu_id and old.scene_code='GUARANTEE'
join tmp_menu_map m on m.old_code=old.menu_code COLLATE utf8mb4_unicode_ci
join bp_menu p on p.scene_code='GUARANTEE' and p.menu_code COLLATE utf8mb4_unicode_ci=m.new_code;
-- 删除旧授权和旧菜单
delete rm from bp_role_menu rm join bp_menu old on old.id=rm.menu_id where old.scene_code='GUARANTEE' and old.menu_code like 'legacy_%';
delete from bp_menu where scene_code='GUARANTEE' and menu_code like 'legacy_%';
drop temporary table tmp_menu_map;
COMMIT;
