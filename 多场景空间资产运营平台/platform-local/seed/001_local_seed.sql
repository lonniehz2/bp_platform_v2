-- 本地演示数据：演示项目（不影响远程环境）
insert ignore into bp_org
(id, tenant_id, parent_id, org_code, org_name, org_type, scene_code, business_mode, address, org_path, sort_no, status, is_deleted)
values
(920000000000010001, '350600', null, 'LOCAL_DEMO', '本地演示项目', 'PROJECT', 'GUARANTEE', 'PUBLIC_RENTAL',
 '本地演示地址', 'LOCAL_DEMO', 1, 'ENABLED', 0);
