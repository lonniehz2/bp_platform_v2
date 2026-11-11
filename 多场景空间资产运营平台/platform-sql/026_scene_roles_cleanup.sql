-- 场景专属角色与测试数据清理

START TRANSACTION;

delete from bp_role_menu where role_id in (select id from bp_role where role_code like 'VERIFY_ROLE_%');

delete from bp_user_role where role_id in (select id from bp_role where role_code like 'VERIFY_ROLE_%');

delete from bp_role_action where role_id in (select id from bp_role where role_code like 'VERIFY_ROLE_%');

delete from bp_role_scope where role_id in (select id from bp_role where role_code like 'VERIFY_ROLE_%');

delete from bp_role_project where role_id in (select id from bp_role where role_code like 'VERIFY_ROLE_%');

delete from bp_role_org where role_id in (select id from bp_role where role_code like 'VERIFY_ROLE_%');

delete from bp_role where role_code like 'VERIFY_ROLE_%';

delete from bp_role_menu where role_id in (select id from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD'));

delete from bp_user_role where role_id in (select id from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD'));

delete from bp_role_action where role_id in (select id from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD'));

delete from bp_role_scope where role_id in (select id from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD'));

delete from bp_role_project where role_id in (select id from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD'));

delete from bp_role_org where role_id in (select id from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD'));

delete from bp_role where scene_code in ('ASSET','SERVICE') and role_code not in ('ASSET_ADMIN','ASSET_MANAGER','ASSET_FINANCE','ASSET_STEWARD','SERVICE_ADMIN','SERVICE_MANAGER','SERVICE_FINANCE','SERVICE_STEWARD');

insert ignore into bp_role(id,tenant_id,scene_code,role_code,role_name,role_status,is_deleted) values
(uuid_short(),'350600','ASSET','ASSET_ADMIN','资产管理员','ENABLED',0),
(uuid_short(),'350600','ASSET','ASSET_MANAGER','资产经理','ENABLED',0),
(uuid_short(),'350600','ASSET','ASSET_FINANCE','资产财务','ENABLED',0),
(uuid_short(),'350600','ASSET','ASSET_STEWARD','资产客服','ENABLED',0),
(uuid_short(),'350600','SERVICE','SERVICE_ADMIN','服务管理员','ENABLED',0),
(uuid_short(),'350600','SERVICE','SERVICE_MANAGER','服务经理','ENABLED',0),
(uuid_short(),'350600','SERVICE','SERVICE_FINANCE','服务财务','ENABLED',0),
(uuid_short(),'350600','SERVICE','SERVICE_STEWARD','服务客服','ENABLED',0);

insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
select uuid_short(),gr.tenant_id,nr.id,am.id from bp_role gr join bp_role nr on nr.tenant_id=gr.tenant_id and nr.scene_code='ASSET' and nr.role_code=replace(gr.role_code,'GUARANTEE','ASSET') join bp_role_menu rm on rm.role_id=gr.id join bp_menu gm on gm.id=rm.menu_id and gm.scene_code='GUARANTEE' join bp_menu am on am.scene_code='ASSET' and am.menu_code=gm.menu_code where gr.scene_code='GUARANTEE' and gr.role_code in ('GUARANTEE_ADMIN','GUARANTEE_MANAGER','GUARANTEE_FINANCE','GUARANTEE_STEWARD');

insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
select uuid_short(),gr.tenant_id,nr.id,am.id from bp_role gr join bp_role nr on nr.tenant_id=gr.tenant_id and nr.scene_code='SERVICE' and nr.role_code=replace(gr.role_code,'GUARANTEE','SERVICE') join bp_role_menu rm on rm.role_id=gr.id join bp_menu gm on gm.id=rm.menu_id and gm.scene_code='GUARANTEE' join bp_menu am on am.scene_code='SERVICE' and am.menu_code=gm.menu_code where gr.scene_code='GUARANTEE' and gr.role_code in ('GUARANTEE_ADMIN','GUARANTEE_MANAGER','GUARANTEE_FINANCE','GUARANTEE_STEWARD');

insert ignore into bp_user_role(id,tenant_id,user_id,role_id)
select uuid_short(),ur.tenant_id,ur.user_id,nr.id from bp_user_role ur join bp_role gr on gr.id=ur.role_id and gr.scene_code='GUARANTEE' join bp_role nr on nr.tenant_id=gr.tenant_id and nr.scene_code='ASSET' and nr.role_code=replace(gr.role_code,'GUARANTEE','ASSET') where gr.role_code in ('GUARANTEE_ADMIN','GUARANTEE_MANAGER','GUARANTEE_FINANCE','GUARANTEE_STEWARD');

insert ignore into bp_user_role(id,tenant_id,user_id,role_id)
select uuid_short(),ur.tenant_id,ur.user_id,nr.id from bp_user_role ur join bp_role gr on gr.id=ur.role_id and gr.scene_code='GUARANTEE' join bp_role nr on nr.tenant_id=gr.tenant_id and nr.scene_code='SERVICE' and nr.role_code=replace(gr.role_code,'GUARANTEE','SERVICE') where gr.role_code in ('GUARANTEE_ADMIN','GUARANTEE_MANAGER','GUARANTEE_FINANCE','GUARANTEE_STEWARD');

delete from bp_user_role where user_id in (select id from bp_user where username like 'VERIFY_USER\_%' or username like 'PWD_USER\_%');

delete from bp_user_scope_override where user_id in (select id from bp_user where username like 'VERIFY_USER\_%' or username like 'PWD_USER\_%');

delete from bp_user where username like 'VERIFY_USER\_%' or username like 'PWD_USER\_%';

COMMIT;
