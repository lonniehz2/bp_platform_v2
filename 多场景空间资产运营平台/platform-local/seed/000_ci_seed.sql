-- CI 专用最小种子：只创建可登录的 admin 与保障房管理员角色
insert ignore into bp_user
(id, tenant_id, username, password_hash, display_name, user_status, is_deleted)
values
(990000000000009001,'350600','admin','$2a$10$hA0eKiDJdf.Z0BzkKWcrbOWPs.mH4vHfDJqSiLTZVqfccD/L305rW','管理员','ENABLED',0);
insert ignore into bp_user_role(id, tenant_id, user_id, role_id)
values (990000000000009002,'350600',990000000000009001,930000000000000001);
