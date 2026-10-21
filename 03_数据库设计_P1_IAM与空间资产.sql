-- =====================================================================
--  云门道业务平台 —— 数据库设计（第三轮）
--  第 1 部分：设计规范 + BC-01 租户与权限 + BC-02 空间资产
--  目标库：MySQL 8.0+  /  InnoDB  /  utf8mb4
--  说明：本文件为设计交付物，可直接执行；执行顺序 P1 → P6
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. 设计规范
-- ---------------------------------------------------------------------
-- 【命名】
--   库名        : bp_platform
--   表前缀      : bp_<bc>_<实体>     bc ∈ {iam,asset,person,grant,biz,fin,dev,ops,flow,rule,msg,rpt,sys}
--   主键        : id           BIGINT UNSIGNED，雪花 ID（应用生成）；字典类小表可用 INT AUTO_INCREMENT
--   外键        : <实体>_id    命名，如 house_id / person_id
--   逻辑删除    : is_deleted    TINYINT(1) 0 否 1 是
--   审计字段    : create_by, create_time, update_by, update_time  （所有业务表必须）
--   多租户      : tenant_id     VARCHAR(32) NOT NULL  （所有业务表必须，且为联合索引首列）
--
-- 【约定】
--   1) 所有业务表必带 tenant_id + 审计字段；禁止物理删除（除日志/临时表）
--   2) 金额统一 DECIMAL(14,2)；比例/费率 DECIMAL(8,4)
--   3) 时间统一 DATETIME(3)；日期用 DATE
--   4) 枚举使用 VARCHAR 存编码（可读、可扩展），字典表 bp_sys_dict 维护
--   5) 状态字段统一 <实体>_status VARCHAR(20)，并在注释中列出取值
--   6) 敏感字段（身份证、手机号、生物特征）落库加密，另存 <字段>_hash 用于精确检索
--   7) 联合索引首列一律 tenant_id；高频查询组合建覆盖索引
--   8) 大表（记录类/日志类）按 create_time 月分区，见各表注释
--
-- 【字符集与排序规则】
--   默认 utf8mb4 / utf8mb4_0900_ai_ci（大小写不敏感）
--   身份证号、卡号等需精确匹配的列使用 utf8mb4_bin

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `bp_platform`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE `bp_platform`;


-- =====================================================================
--  BC-01  租户与权限（iam）
-- =====================================================================

-- 1.1 租户（区县级 / 运营主体）
CREATE TABLE `bp_iam_tenant` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键（雪花ID）',
  `tenant_code`    VARCHAR(32)     NOT NULL COMMENT '租户编码（全局唯一，用于数据隔离与配置）',
  `tenant_name`    VARCHAR(128)    NOT NULL COMMENT '租户名称（如"漳州市住房保障中心"）',
  `tenant_type`    VARCHAR(20)     NOT NULL DEFAULT 'ORG' COMMENT '类型：GOV 政府 / ORG 运营主体 / ENTERPRISE 企业',
  `parent_id`      BIGINT UNSIGNED NULL     COMMENT '上级租户ID（支持多级，NULL 为顶级）',
  `region_code`    VARCHAR(20)     NULL     COMMENT '行政区划编码（GB/T 2260）',
  `isolation_mode` VARCHAR(20)     NOT NULL DEFAULT 'ROW' COMMENT '数据隔离模式：ROW 行级 / SCHEMA 独立Schema / DB 独立库',
  `schema_name`    VARCHAR(64)     NULL     COMMENT 'isolation_mode=SCHEMA 时的库名',
  `contact_name`   VARCHAR(64)     NULL     COMMENT '联系人',
  `contact_phone`  VARCHAR(32)     NULL     COMMENT '联系电话',
  `expire_date`    DATE            NULL     COMMENT '有效期（SaaS 场景）',
  `status`         VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `config_json`    JSON            NULL     COMMENT '租户级配置（场景包、阈值、开关等）',
  `remark`         VARCHAR(500)    NULL     COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_code` (`tenant_code`),
  KEY `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户（区县级/运营主体）';

-- 1.2 组织（树形；承载行政层级与项目层级）
CREATE TABLE `bp_iam_org` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `org_code`     VARCHAR(64)     NOT NULL COMMENT '组织编码（租户内唯一）',
  `org_name`     VARCHAR(128)    NOT NULL COMMENT '组织名称（如小区名、项目名）',
  `parent_id`    BIGINT UNSIGNED NULL     COMMENT '上级组织ID',
  `org_path`     VARCHAR(1000)   NOT NULL DEFAULT '' COMMENT '组织路径（祖先ID链，逗号分隔，用于子树查询）',
  `org_level`    INT             NOT NULL DEFAULT 1 COMMENT '层级（1 起）',
  `org_type`     VARCHAR(30)     NOT NULL COMMENT '组织类型：CITY 市 / DISTRICT 区县 / PROJECT 项目 / COMMUNITY 小区 / PARK 园区 / CAMPUS 校园 / COMPANY 企业 / DEPT 部门',
  `supervise_type` VARCHAR(30)   NULL     COMMENT '监管类别：NONE 无 / POLICE 公安 / FIRE 消防 / HOUSING 住建 / CIVIL 民政 / STREET 街道 / COMMUNITY 社区服务',
  `address`      VARCHAR(255)    NULL     COMMENT '地址',
  `longitude`    DECIMAL(11,7)   NULL     COMMENT '经度',
  `latitude`     DECIMAL(11,7)   NULL     COMMENT '纬度',
  `contact_name` VARCHAR(64)     NULL     COMMENT '联系人',
  `contact_phone` VARCHAR(32)     NULL     COMMENT '联系电话',
  `sort_no`      INT             NOT NULL DEFAULT 0 COMMENT '排序',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED',
  `remark`       VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`    VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`    VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_orgcode` (`tenant_id`,`org_code`,`is_deleted`),
  KEY `idx_tenant_parent` (`tenant_id`,`parent_id`),
  KEY `idx_tenant_path` (`tenant_id`,`org_path`(255)),
  KEY `idx_tenant_type` (`tenant_id`,`org_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组织（树形，承载行政与项目层级）';

-- 1.3 用户
CREATE TABLE `bp_iam_user` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `username`      VARCHAR(64)     NOT NULL COMMENT '登录名',
  `password_hash` VARCHAR(128)    NOT NULL COMMENT '密码哈希（BCrypt）',
  `pwd_update_time` DATETIME(3)   NULL     COMMENT '密码修改时间（用于强制定期改密）',
  `real_name`     VARCHAR(64)     NULL     COMMENT '姓名',
  `phone`         VARCHAR(32)     NULL     COMMENT '手机号（加密存储）',
  `phone_hash`    VARCHAR(64)     NULL     COMMENT '手机号哈希（精确检索用）',
  `email`         VARCHAR(128)    NULL COMMENT '邮箱',
  `avatar`        VARCHAR(500)    NULL     COMMENT '头像URL',
  `person_id`     BIGINT UNSIGNED NULL     COMMENT '关联人员档案ID（BC-03）',
  `org_id`        BIGINT UNSIGNED NULL     COMMENT '主属组织ID',
  `user_type`     VARCHAR(30)     NOT NULL DEFAULT 'STAFF' COMMENT '类型：STAFF 员工 / TENANT 租户 / GOV 监管 / PLATFORM 平台',
  `is_admin`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否管理员',
  `single_device` TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否限制单设备登录：1 是 0 否',
  `device_id`     VARCHAR(128)    NULL     COMMENT '当前绑定设备标识（单设备登录限制用）',
  `last_login_time` DATETIME(3)   NULL COMMENT '最后登录时间',
  `last_login_ip`   VARCHAR(64)   NULL COMMENT '最后登录IP',
  `login_count`   INT             NOT NULL DEFAULT 0 COMMENT '登录次数',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED / LOCKED',
  `remark`        VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_username` (`tenant_id`,`username`,`is_deleted`),
  KEY `idx_tenant_phone` (`tenant_id`,`phone_hash`),
  KEY `idx_tenant_org` (`tenant_id`,`org_id`),
  KEY `idx_person` (`person_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户';

-- 1.4 角色
CREATE TABLE `bp_iam_role` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `role_code`   VARCHAR(64)     NOT NULL COMMENT '角色编码',
  `role_name`   VARCHAR(128)    NOT NULL COMMENT '角色名称（如"受理岗""审核岗""财务岗"）',
  `role_type`   VARCHAR(30)     NOT NULL DEFAULT 'CUSTOM' COMMENT '类型：SYSTEM 系统内置 / CUSTOM 自定义',
  `data_scope`  VARCHAR(30)     NOT NULL DEFAULT 'SELF' COMMENT '数据范围：ALL 全部 / TENANT 本租户 / ORG 本组织 / ORG_TREE 本组织及下级 / PROJECT 本项目 / SPACE 本空间及子空间 / SELF 仅本人',
  `sort_no`     INT             NOT NULL DEFAULT 0 COMMENT '排序号',
  `status`      VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `remark`      VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`   VARCHAR(64)     NULL COMMENT '创建人',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`   VARCHAR(64)     NULL COMMENT '更新人',
  `update_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_rolecode` (`tenant_id`,`role_code`,`is_deleted`),
  KEY `idx_tenant` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色';

-- 1.5 权限资源（菜单/按钮/接口/字段级）
CREATE TABLE `bp_iam_permission` (
  `id`         BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `parent_id`  BIGINT UNSIGNED NULL     COMMENT '上级权限ID',
  `perm_code`  VARCHAR(128)    NOT NULL COMMENT '权限标识码（如 asset:house:edit）',
  `perm_name`  VARCHAR(128)    NOT NULL COMMENT '权限名称',
  `perm_type`  VARCHAR(20)     NOT NULL COMMENT '类型：MENU 菜单 / BUTTON 按钮 / API 接口 / FIELD 字段',
  `route_path` VARCHAR(255)    NULL     COMMENT '前端路由',
  `component`  VARCHAR(255)    NULL     COMMENT '前端组件',
  `icon`       VARCHAR(64)     NULL COMMENT '图标',
  `scenario`   VARCHAR(30)     NULL     COMMENT '所属场景包（NULL 为内核通用）：PUBLIC_HOUSING / APARTMENT / DORMITORY / HOTEL / RENTAL / PROPERTY',
  `sort_no`    INT             NOT NULL DEFAULT 0 COMMENT '排序号',
  `status`     VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `create_time` DATETIME(3)    NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_perm_code` (`perm_code`),
  KEY `idx_parent` (`parent_id`),
  KEY `idx_scenario` (`scenario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限资源（菜单/按钮/接口/字段）';

-- 1.6 角色-权限
CREATE TABLE `bp_iam_role_permission` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `role_id`       BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
  `permission_id` BIGINT UNSIGNED NOT NULL COMMENT '权限ID',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_perm` (`tenant_id`,`role_id`,`permission_id`),
  KEY `idx_perm` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色-权限关系';

-- 1.7 用户-角色-组织（支持同一用户在不同组织下不同角色）
CREATE TABLE `bp_iam_user_role` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `user_id`     BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `role_id`     BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
  `org_id`      BIGINT UNSIGNED NULL     COMMENT '角色生效的组织范围',
  `create_by`   VARCHAR(64)     NULL COMMENT '创建人',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_role_org` (`tenant_id`,`user_id`,`role_id`,`org_id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_role` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户-角色-组织关系';

-- 1.8 多账套（财务主体隔离）
CREATE TABLE `bp_iam_account_set` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `set_code`     VARCHAR(64)     NOT NULL COMMENT '账套编码',
  `set_name`     VARCHAR(128)    NOT NULL COMMENT '账套名称',
  `org_id`       BIGINT UNSIGNED NULL     COMMENT '归属组织',
  `currency`     VARCHAR(8)      NOT NULL DEFAULT 'CNY' COMMENT '币种（默认 CNY）',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `is_deleted`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`    VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`    VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_setcode` (`tenant_id`,`set_code`,`is_deleted`),
  KEY `idx_org` (`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账套（多财务主体隔离）';

-- 1.9 会话（单设备登录、强制下线）
CREATE TABLE `bp_iam_session` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `user_id`      BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `token_id`     VARCHAR(64)     NOT NULL COMMENT '令牌标识（JWT jti）',
  `device_type`  VARCHAR(30)     NULL     COMMENT '设备类型：WEB / APP / MINIAPP / SCREEN',
  `device_id`    VARCHAR(128)    NULL     COMMENT '设备标识',
  `login_ip`     VARCHAR(64)     NULL COMMENT '登录IP',
  `login_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '登录时间',
  `expire_time`  DATETIME(3)     NOT NULL COMMENT '过期时间',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE / LOGOUT / KICKED / EXPIRED',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_token` (`token_id`),
  KEY `idx_tenant_user` (`tenant_id`,`user_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录会话（单设备登录与强制下线）';


-- =====================================================================
--  BC-02  空间资产（asset）
-- =====================================================================

-- 2.1 空间节点（统一树：片区→楼栋→单元→楼层→房间→床位）
CREATE TABLE `bp_asset_space` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `org_id`        BIGINT UNSIGNED NOT NULL COMMENT '归属组织（项目/小区）',
  `parent_id`     BIGINT UNSIGNED NULL     COMMENT '上级空间ID',
  `space_code`    VARCHAR(64)     NOT NULL COMMENT '空间编码（同组织内唯一）',
  `space_name`    VARCHAR(128)    NOT NULL COMMENT '空间名称（如"1幢2单元501"）',
  `space_type`    VARCHAR(30)     NOT NULL COMMENT '类型：AREA 片区 / BUILDING 楼栋 / UNIT 单元 / FLOOR 楼层 / ROOM 房间 / BED 床位 / PARKING 车位 / GARAGE 车库 / SITE 场地',
  `space_path`    VARCHAR(1000)   NOT NULL DEFAULT '' COMMENT '空间路径（祖先ID链，用于权限继承与子树查询）',
  `path_code`     VARCHAR(500)    NOT NULL DEFAULT '' COMMENT '空间路径编码（如 01/02/01）',
  `space_level`   INT             NOT NULL DEFAULT 1 COMMENT '层级（1 起）',
  `full_name`     VARCHAR(500)    NULL     COMMENT '全路径名称（如"金麓小区B9幢9单元401室"）',
  `area`          DECIMAL(12,2)   NULL     COMMENT '面积（㎡）',
  `sort_no`       INT             NOT NULL DEFAULT 0 COMMENT '排序号',
  `location_code` VARCHAR(64)     NULL     COMMENT '五级地址编码',
  `is_public`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否公共区域',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED',
  `remark`        VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_spacecode` (`tenant_id`,`space_code`,`is_deleted`),
  KEY `idx_tenant_org_type` (`tenant_id`,`org_id`,`space_type`),
  KEY `idx_tenant_parent` (`tenant_id`,`parent_id`),
  KEY `idx_tenant_pathcode` (`tenant_id`,`path_code`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='空间节点（统一树：片区→楼栋→单元→楼层→房间→床位）';

-- 2.2 房源（面向配租的业务实体，与空间节点一对一或一对多）
CREATE TABLE `bp_asset_house` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `org_id`         BIGINT UNSIGNED NOT NULL COMMENT '归属组织',
  `space_id`       BIGINT UNSIGNED NOT NULL COMMENT '关联空间节点（ROOM 类型）',
  `house_code`     VARCHAR(64)     NOT NULL COMMENT '房源编号（对外展示，同组织唯一）',
  `house_name`     VARCHAR(128)    NOT NULL COMMENT '房源名称',
  `house_type`     VARCHAR(30)     NOT NULL COMMENT '房源类型：PUBLIC_RENTAL 公租房 / AFFORDABLE_RENTAL 保租房 / TALENT 人才公寓 / APARTMENT 公寓 / DORMITORY 宿舍 / RENTAL 出租房 / HOTEL 酒店民宿',
  -- 建筑属性
  `struct_type`    VARCHAR(30)     NULL     COMMENT '建筑类型：VILLA 排屋别墅 / MULTI 多层 / SMALL_HIGH 小高层 / HIGH 高层 / SUPER_HIGH 超高层',
  `use_type`       VARCHAR(20)     NULL     COMMENT '用途：CIVIL 民用 / COMMERCIAL 商用',
  `unit_layout`    VARCHAR(30)     NULL     COMMENT '户型：1/2/3/4 居',
  `floor_no`       INT             NULL     COMMENT '所在楼层',
  `orientation`    VARCHAR(20)     NULL     COMMENT '朝向',
  `area`           DECIMAL(12,2)   NULL     COMMENT '建筑面积（㎡）',
  `inner_area`     DECIMAL(12,2)   NULL     COMMENT '套内面积（㎡）',
  `decoration`     VARCHAR(30)     NULL     COMMENT '装修：ROUGH 毛坯 / SIMPLE 简装 / FINE 精装',
  -- 保障房属性
  `security_type`  VARCHAR(30)     NULL     COMMENT '保障类别（保障房专用）：LOW_RENT 廉租 / PUBLIC 公租 / AFFORDABLE 保租 / TALENT 人才',
  `rent_standard`  DECIMAL(14,2)   NULL     COMMENT '政策租金标准（元/㎡·月 或 元/月，按 rent_unit 解释）',
  `rent_unit`      VARCHAR(20)     NULL     COMMENT '租金计价单位：AREA_MONTH 元/㎡·月 / HOUSE_MONTH 元/套·月 / BED_MONTH 元/床·月 / HOUSE_NIGHT 元/套·夜',
  `max_capacity`   INT             NULL     COMMENT '最大入住人数',
  `current_capacity` INT           NOT NULL DEFAULT 0 COMMENT '已入住人数',
  -- 状态
  `house_status`   VARCHAR(30)     NOT NULL DEFAULT 'PENDING_ALLOC' COMMENT '房源状态：PENDING_ALLOC 待分配 / LOCKED 锁定中 / ALLOCATED 已配租 / OCCUPIED 已入住 / VACANT 空置待配 / MAINTENANCE 维修中 / DISABLED 停用',
  `use_status`     VARCHAR(30)     NULL     COMMENT '使用状态（资产口径）：IDLE 闲置 / IN_USE 在用 / RENTED 出租',
  `manage_nature`  VARCHAR(30)     NULL     COMMENT '经营性质：SELF 自营 / ENTRUST 委托 / LEASE 租赁',
  `property_nature` VARCHAR(30)    NULL     COMMENT '产权性质：STATE 国有 / COLLECTIVE 集体 / PRIVATE 私有',
  `owner_org_id`   BIGINT UNSIGNED NULL     COMMENT '产权方组织（保障房为政府/运营公司）',
  `admin_org_id`   BIGINT UNSIGNED NULL     COMMENT '管理方组织',
  -- 其他
  `house_alias`    VARCHAR(64)     NULL     COMMENT '房源别名',
  `third_room_no`  VARCHAR(64)     NULL     COMMENT '第三方房间编号（对接公租房信息系统用）',
  `lock_status_time` DATETIME(3)   NULL     COMMENT '状态最近变更时间',
  -- 存量迁移与追溯（见《数据库设计说明》附录「存量数据迁移方案」，二期执行）
  `owner_person_id` BIGINT UNSIGNED NULL    COMMENT '户主（自然人）：★实测老数据"户主姓名/手机号"为自然人，故与 owner_org_id 并存',
  `legacy_house_id` VARCHAR(64)    NULL     COMMENT '存量来源房源ID（追溯老平台 w_base_house.house_id）',
  `legacy_source`  VARCHAR(40)     NULL     COMMENT '存量来源系统：YMD_IOT / PROPERTY_OLD / IMPORT',
  `migrate_batch`  VARCHAR(64)     NULL     COMMENT '迁移批次号（可回滚）',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_housecode` (`tenant_id`,`house_code`,`is_deleted`),
  UNIQUE KEY `uk_legacy_house` (`tenant_id`,`legacy_source`,`legacy_house_id`),
  KEY `idx_tenant_org_status` (`tenant_id`,`org_id`,`house_status`),
  KEY `idx_tenant_space` (`tenant_id`,`space_id`),
  KEY `idx_tenant_type` (`tenant_id`,`house_type`),
  KEY `idx_tenant_third_room` (`tenant_id`,`third_room_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='房源（配租业务实体）';

-- 2.3 车位
CREATE TABLE `bp_asset_parking` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `org_id`         BIGINT UNSIGNED NOT NULL COMMENT '组织ID',
  `space_id`       BIGINT UNSIGNED NULL     COMMENT '关联空间节点（PARKING）',
  `garage_id`      BIGINT UNSIGNED NULL     COMMENT '所属车库空间ID',
  `parking_code`   VARCHAR(64)     NOT NULL COMMENT '车位编号',
  `parking_type`   VARCHAR(30)     NOT NULL DEFAULT 'PRIVATE' COMMENT '类型：PRIVATE 私人 / RENT 出租 / SHARE 共享 / PUBLIC 公共',
  `parking_status` VARCHAR(30)     NOT NULL DEFAULT 'IDLE' COMMENT '状态：IDLE 空闲 / OCCUPIED 已占用 / DISABLED 停用 / LOCKED 锁定',
  `area`           DECIMAL(10,2)   NULL COMMENT '面积（㎡）',
  `owner_person_id` BIGINT UNSIGNED NULL    COMMENT '车位所有者（人员ID）',
  `plate_no`       VARCHAR(32)     NULL     COMMENT '绑定车牌（可多个，逗号分隔）',
  `rent_price`     DECIMAL(14,2)   NULL     COMMENT '租赁单价',
  `auth_beg`       DATE            NULL     COMMENT '授权开始',
  `auth_end`       DATE            NULL     COMMENT '授权结束',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_parkingcode` (`tenant_id`,`parking_code`,`is_deleted`),
  KEY `idx_tenant_org_status` (`tenant_id`,`org_id`,`parking_status`),
  KEY `idx_garage` (`garage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='车位';

-- 2.4 空间-设备绑定关系（业务视图，设备主数据在 IoT 平台）
CREATE TABLE `bp_asset_space_device` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `space_id`    BIGINT UNSIGNED NOT NULL COMMENT '空间ID',
  `house_id`    BIGINT UNSIGNED NULL     COMMENT '房源ID（便于按房源查设备）',
  `device_id`   VARCHAR(64)     NOT NULL COMMENT '设备ID（IoT 平台侧标识）',
  `device_mac`  VARCHAR(64)     NULL     COMMENT '设备MAC',
  `device_type` VARCHAR(30)     NOT NULL COMMENT '设备类型：LOCK 门锁 / ACCESS 门禁 / ELEVATOR 梯控 / GATE 道闸 / METER_W 水表 / METER_E 电表 / METER_G 燃气表 / GATEWAY 网关 / COLLECTOR 采集器',
  `bind_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '绑定时间',
  `unbind_time` DATETIME(3)     NULL     COMMENT '解绑时间',
  `is_active`   TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否当前有效绑定',
  `create_by`   VARCHAR(64)     NULL COMMENT '创建人',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_device` (`tenant_id`,`device_id`,`is_active`),
  KEY `idx_tenant_space` (`tenant_id`,`space_id`,`is_active`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`,`is_active`),
  KEY `idx_tenant_type` (`tenant_id`,`device_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='空间-设备绑定关系（业务视图）';

-- 2.5 空间-人员占用关系（谁住哪，支撑权限继承与走访核查）
CREATE TABLE `bp_asset_space_occupancy` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `space_id`      BIGINT UNSIGNED NOT NULL COMMENT '空间ID（通常为 ROOM 或 BED）',
  `house_id`      BIGINT UNSIGNED NULL     COMMENT '房源ID',
  `person_id`     BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `occupy_type`   VARCHAR(30)     NOT NULL COMMENT '占用类型：TENANT 承租人 / COHABITANT 同住人 / FAMILY 家庭成员 / BED 床位入住 / VISITOR 访客',
  `is_primary`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否主承租人',
  `start_date`    DATE            NOT NULL COMMENT '开始日期',
  `end_date`      DATE            NULL     COMMENT '结束日期（NULL 表示当前有效）',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE 有效 / ENDED 已结束',
  `source_type`   VARCHAR(30)     NULL     COMMENT '来源：CONTRACT 合同 / MANUAL 手工 / IMPORT 导入 / HR_SYNC HR同步',
  `source_id`     BIGINT UNSIGNED NULL     COMMENT '来源单据ID',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_space_active` (`tenant_id`,`space_id`,`status`),
  KEY `idx_tenant_person_active` (`tenant_id`,`person_id`,`status`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='空间-人员占用关系';

-- 2.6 资产导入批次（批量导入留痕与回滚）
CREATE TABLE `bp_asset_import_batch` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `batch_no`      VARCHAR(64)     NOT NULL COMMENT '批次号',
  `import_type`   VARCHAR(30)     NOT NULL COMMENT '导入类型：SPACE 空间 / HOUSE 房源 / PARKING 车位 / PERSON 人员',
  `file_url`      VARCHAR(500)    NOT NULL COMMENT '源文件URL',
  `total_count`   INT             NOT NULL DEFAULT 0 COMMENT '总数',
  `success_count` INT             NOT NULL DEFAULT 0 COMMENT '成功数',
  `fail_count`    INT             NOT NULL DEFAULT 0 COMMENT '失败数',
  `error_url`     VARCHAR(500)    NULL     COMMENT '错误明细文件URL',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'PROCESSING' COMMENT '状态：PROCESSING 处理中 / SUCCESS 成功 / PARTIAL 部分成功 / FAILED 失败 / ROLLED_BACK 已回滚',
  `operator_id`   BIGINT UNSIGNED NULL COMMENT '操作人ID',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_batchno` (`tenant_id`,`batch_no`),
  KEY `idx_tenant_type` (`tenant_id`,`import_type`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产导入批次（留痕与回滚）';

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- P1 完成：BC-01 租户与权限（9 表）、BC-02 空间资产（6 表）= 15 表
-- ---------------------------------------------------------------------
