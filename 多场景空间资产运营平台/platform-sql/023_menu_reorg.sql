-- 菜单重组：按租务、合同、房源、数据报表分层
-- 仅调整分组名称、父级、排序；不改菜单编码和角色授权关系

insert into bp_menu(id, scene_code, menu_code, parent_code, menu_name, menu_type, route, sort_no, menu_status)
values (921000000000000010, 'GUARANTEE', 'group_data', null, '数据与报表', 'GROUP', null, 90, 'ENABLED')
on duplicate key update menu_name='数据与报表', sort_no=90, menu_status='ENABLED';

update bp_menu set menu_name='租务管理', sort_no=20 where menu_code='group_application';
update bp_menu set menu_name='合同管理', sort_no=30 where menu_code='group_contract';
update bp_menu set menu_name='房源与资产', sort_no=40 where menu_code='group_asset';
update bp_menu set menu_name='收费与账务', sort_no=50 where menu_code='group_finance';
update bp_menu set menu_name='服务与监督', sort_no=60 where menu_code='group_service';
update bp_menu set menu_name='通行与设备', sort_no=70 where menu_code='group_access';
update bp_menu set menu_name='风险与预警', sort_no=80 where menu_code='group_risk';
update bp_menu set menu_name='数据与报表', sort_no=90 where menu_code='group_data';
update bp_menu set menu_name='系统管理', sort_no=100 where menu_code='group_system';

-- 租务管理：合并轮候与配租
update bp_menu set parent_code='group_application', sort_no=80 where menu_code='waitlist';
update bp_menu set parent_code='group_application', sort_no=90 where menu_code='allocations';
update bp_menu set parent_code='group_application', sort_no=100 where menu_code='publicities';
update bp_menu set parent_code='group_application', sort_no=50 where menu_code='applications';
update bp_menu set parent_code='group_application', sort_no=60 where menu_code='person';
update bp_menu set parent_code='group_application', sort_no=70 where menu_code='qualification';
delete from bp_menu where menu_code='group_waitlist';

-- 房源与资产：空间/房源/日房态/房源展示顺序
update bp_menu set sort_no=210 where menu_code='asset';
update bp_menu set sort_no=220 where menu_code='spaces';
update bp_menu set sort_no=230 where menu_code='houses';
update bp_menu set sort_no=240 where menu_code='calendar';
update bp_menu set sort_no=250 where menu_code='listings';
update bp_menu set sort_no=260 where menu_code='shortrent';

-- 恢复组织机构（避免历史 ID 冲突）
update bp_menu set menu_name='组织机构', route='/guarantee/orgs', parent_code='group_system', sort_no=10 where menu_code='orgs';

-- 工作台：工作台、运营驾驶舱、统一查询、待办、审批、消息
insert into bp_menu(id, scene_code, menu_code, parent_code, menu_name, menu_type, route, sort_no, menu_status)
values (922000000000000049, 'GUARANTEE', 'cockpit', 'group_workbench', '运营驾驶舱', 'PAGE', '/guarantee/cockpit', 20, 'ENABLED')
on duplicate key update parent_code='group_workbench', menu_name='运营驾驶舱', route='/guarantee/cockpit', sort_no=20, menu_status='ENABLED';
update bp_menu set sort_no=10, route='/guarantee/workbench' where menu_code='dashboard';
update bp_menu set sort_no=30 where menu_code='search';
update bp_menu set sort_no=40 where menu_code='todos';
update bp_menu set parent_code='group_workbench', sort_no=50 where menu_code='audit';
update bp_menu set sort_no=60 where menu_code='message';

-- 数据与报表：报表中心、监管报送
update bp_menu set parent_code='group_data', menu_name='报表中心', sort_no=10 where menu_code='reports';
update bp_menu set parent_code='group_data', sort_no=20 where menu_code='gov';

-- 房源通行归入通行与设备
update bp_menu set parent_code='group_access', sort_no=70 where menu_code='houseAccess';

-- 系统管理：只保留后台配置
update bp_menu set parent_code='group_system', sort_no=10 where menu_code='orgs';
update bp_menu set parent_code='group_system', sort_no=20 where menu_code='rbac';
update bp_menu set parent_code='group_system', sort_no=30 where menu_code='batchImport';
update bp_menu set parent_code='group_system', sort_no=40 where menu_code='sys';
update bp_menu set parent_code='group_system', sort_no=50 where menu_code='help';

-- 运营驾驶舱对全部现有角色开放，数据仍受角色数据范围约束
insert ignore into bp_role_menu(id, tenant_id, role_id, menu_id)
select 980000000000000000 + row_number() over (order by r.id), r.tenant_id, r.id, m.id
from bp_role r join bp_menu m on m.menu_code='cockpit'
where r.scene_code='GUARANTEE' and r.is_deleted=0 and m.menu_status='ENABLED';
