-- 为已有角色补齐其页面权限下的全部功能权限
insert ignore into bp_role_action(role_id, menu_code, action_code)
select rm.role_id, m.menu_code, a.action_code
from bp_role_menu rm
join bp_menu m on m.id = rm.menu_id
join (
  select 'view' action_code
  union all select 'create'
  union all select 'edit'
  union all select 'delete'
  union all select 'approve'
) a
where m.menu_type = 'PAGE' and m.menu_status = 'ENABLED';
