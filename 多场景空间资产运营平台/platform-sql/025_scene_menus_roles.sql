-- 为 ASSET / SERVICE 场景复制可用菜单与角色模板

START TRANSACTION;

insert ignore into bp_menu(id,scene_code,menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status)
select uuid_short(),'ASSET',menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status from bp_menu where scene_code='GUARANTEE';

insert ignore into bp_role(id,tenant_id,scene_code,role_code,role_name,role_status,is_deleted)
select uuid_short(),tenant_id,'ASSET',role_code,role_name,role_status,is_deleted from bp_role where scene_code='GUARANTEE';

insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
select uuid_short(),r.tenant_id,ar.id,am.id from bp_role r join bp_role ar on ar.tenant_id=r.tenant_id and ar.scene_code='ASSET' and ar.role_code=r.role_code join bp_role_menu rm on rm.role_id=r.id join bp_menu gm on gm.id=rm.menu_id and gm.scene_code='GUARANTEE' join bp_menu am on am.scene_code='ASSET' and am.menu_code=gm.menu_code where r.scene_code='GUARANTEE';

insert ignore into bp_menu(id,scene_code,menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status)
select uuid_short(),'SERVICE',menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status from bp_menu where scene_code='GUARANTEE';

insert ignore into bp_role(id,tenant_id,scene_code,role_code,role_name,role_status,is_deleted)
select uuid_short(),tenant_id,'SERVICE',role_code,role_name,role_status,is_deleted from bp_role where scene_code='GUARANTEE';

insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
select uuid_short(),r.tenant_id,ar.id,am.id from bp_role r join bp_role ar on ar.tenant_id=r.tenant_id and ar.scene_code='SERVICE' and ar.role_code=r.role_code join bp_role_menu rm on rm.role_id=r.id join bp_menu gm on gm.id=rm.menu_id and gm.scene_code='GUARANTEE' join bp_menu am on am.scene_code='SERVICE' and am.menu_code=gm.menu_code where r.scene_code='GUARANTEE';

insert ignore into bp_user_role(id,tenant_id,user_id,role_id)
select uuid_short(),ur.tenant_id,ur.user_id,ar.id from bp_user_role ur join bp_role gr on gr.id=ur.role_id and gr.scene_code='GUARANTEE' join bp_role ar on ar.tenant_id=gr.tenant_id and ar.scene_code='ASSET' and ar.role_code=gr.role_code;

insert ignore into bp_user_role(id,tenant_id,user_id,role_id)
select uuid_short(),ur.tenant_id,ur.user_id,ar.id from bp_user_role ur join bp_role gr on gr.id=ur.role_id and gr.scene_code='GUARANTEE' join bp_role ar on ar.tenant_id=gr.tenant_id and ar.scene_code='SERVICE' and ar.role_code=gr.role_code;

COMMIT;
