-- 本地全新数据库初始化：001 已包含当前完整 schema；003~017 仅用于旧库升级
source /sql/001_platform_core.sql;
source /sql/002_menu_seed.sql;
source /sql/006_house_attribute_extensions.sql;
source /sql/010_device_import_extensions.sql;
source /sql/013_refund.sql;
source /sql/015_listing_booking.sql;
source /sql/016_listing_order.sql;
source /sql/017_audit_log.sql;
source /sql/018_menu_unify.sql;
source /sql/019_role_data_scope.sql;
source /sql/020_role_action.sql;
source /sql/021_role_action_menu.sql;
source /sql/022_backfill_role_actions.sql;
source /compat/01_local_compat.sql;
source /seed/001_local_seed.sql;
source /seed/002_demo_full.sql;
