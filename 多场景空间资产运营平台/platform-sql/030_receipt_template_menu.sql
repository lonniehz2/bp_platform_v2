-- 收据模板菜单
insert ignore into bp_menu(id,scene_code,menu_code,parent_code,menu_name,menu_type,route,sort_no,menu_status) values
(922000000000000091,'GUARANTEE','receiptTemplates','group_system','收据模板','PAGE','/guarantee/receipt-templates',60,'ENABLED'),
(922000000000000092,'ASSET','receiptTemplates','group_system','收据模板','PAGE','/guarantee/receipt-templates',60,'ENABLED'),
(922000000000000093,'SERVICE','receiptTemplates','group_system','收据模板','PAGE','/guarantee/receipt-templates',60,'ENABLED');
insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
select uuid_short(), r.tenant_id, r.id, m.id from bp_role r join bp_menu m on m.scene_code=r.scene_code and m.menu_code='receiptTemplates'
where r.role_code in ('GUARANTEE_ADMIN','GUARANTEE_MANAGER','ASSET_ADMIN','ASSET_MANAGER','SERVICE_ADMIN','SERVICE_MANAGER');
