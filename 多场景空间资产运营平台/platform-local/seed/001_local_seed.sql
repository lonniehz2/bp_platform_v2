-- 本地演示数据：演示项目（不影响远程环境）
insert ignore into bp_org
(id, tenant_id, parent_id, org_code, org_name, org_type, scene_code, business_mode, address, org_path, sort_no, status, is_deleted)
values
(920000000000010001, '350600', null, 'LOCAL_DEMO', '本地演示项目', 'PROJECT', 'GUARANTEE', 'PUBLIC_RENTAL',
 '本地演示地址', 'LOCAL_DEMO', 1, 'ENABLED', 0);

insert ignore into bp_migration_exception
(id, source_table, source_id, reason, payload, resolve_status, resolution, resolved_by, resolved_time)
values
(920000000000020001, 'LOCAL_SEED', 1, '本地种子数据：已处理迁移异常', null, 'RESOLVED', 'ACCEPT_SKIP', 'local', now());
