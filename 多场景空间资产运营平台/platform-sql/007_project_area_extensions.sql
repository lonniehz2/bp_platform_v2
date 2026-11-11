-- 项目面积产权字段扩展（已有库升级用）
-- 新库 001_platform_core.sql 已包含这些字段；本文件只用于旧库补列。

-- 幂等补列：新库已包含字段时跳过
drop procedure if exists add_column_if_missing;
delimiter //
create procedure add_column_if_missing(in tbl varchar(64), in col varchar(64), in ddl varchar(255))
begin
  if not exists (select 1 from information_schema.columns where table_schema=database() and table_name=tbl and column_name=col) then
    set @ddl = concat('alter table `', tbl, '` add column `', col, '` ', ddl);
    prepare stmt from @ddl;
    execute stmt;
    deallocate prepare stmt;
  end if;
end//
delimiter ;

call add_column_if_missing('bp_org','total_area','decimal(12,2) null');
call add_column_if_missing('bp_org','land_area','decimal(12,2) null');
call add_column_if_missing('bp_org','property_type','varchar(32) null');
call add_column_if_missing('bp_org','build_year','int null');

drop procedure if exists add_column_if_missing;
