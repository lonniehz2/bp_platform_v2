-- 审批流程组织级覆盖（已有库升级用，幂等）
drop procedure if exists add_column_if_missing;
delimiter //
create procedure add_column_if_missing(in tbl varchar(64), in col varchar(64), in ddl varchar(255))
begin
  if not exists (select 1 from information_schema.columns where table_schema=database() and table_name=tbl and column_name=col) then
    set @ddl = concat('alter table `', tbl, '` add column `', col, '` ', ddl);
    prepare stmt from @ddl; execute stmt; deallocate prepare stmt;
  end if;
end//
delimiter ;
call add_column_if_missing('bp_wf_flow','org_id','bigint null comment ''组织ID，空表示场景默认流程'' after biz_type');
drop procedure if exists add_column_if_missing;
set @idx = (select count(*) from information_schema.statistics where table_schema=database() and table_name='bp_wf_flow' and index_name='idx_wf_flow_org');
set @sql = if(@idx=0, 'create index idx_wf_flow_org on bp_wf_flow (tenant_id, scene_code, biz_type, org_id)', 'select 1');
prepare stmt from @sql; execute stmt; deallocate prepare stmt;
