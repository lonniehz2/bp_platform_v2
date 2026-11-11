-- 隐藏历史验证项目，避免进入报表和演示列表
update bp_org set is_deleted=1, update_time=now() where org_code like 'VERIFY\_PROJ\_%';
