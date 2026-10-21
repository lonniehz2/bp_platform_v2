-- =====================================================================
--  云门道业务平台 —— 数据库设计（第三轮）
--  第 4 部分：BC-07 设备与通信  +  BC-08 告警与工单
--  目标库：MySQL 8.0+  /  InnoDB  /  utf8mb4
--  注意：本部分含【分区表】，请确认 MySQL 版本 ≥ 8.0 且已开启分区支持
-- =====================================================================

SET NAMES utf8mb4;
USE `bp_platform`;


-- =====================================================================
--  BC-07  设备与通信（dev）
-- =====================================================================

-- 7.1 设备业务视图（主数据在 IoT 平台，本表存业务属性与状态缓存）
CREATE TABLE `bp_dev_device` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `device_id`        VARCHAR(64)     NOT NULL COMMENT '设备ID（IoT 平台侧标识）',
  `device_mac`       VARCHAR(64)     NULL     COMMENT '设备MAC',
  `device_name`      VARCHAR(128)    NULL     COMMENT '设备名称',
  `device_type`      VARCHAR(30)     NOT NULL COMMENT '设备类型：LOCK 门锁 / ACCESS 门禁 / ELEVATOR 梯控 / GATE 道闸 / METER_W 水表 / METER_E 电表 / METER_G 燃气表 / GATEWAY 网关 / COLLECTOR 采集器 / BOX 车闸盒子 / VISITOR_CTRL 访客码控制器',
  `device_model`     VARCHAR(64)     NULL     COMMENT '设备型号',
  `lock_type`        VARCHAR(30)     NULL     COMMENT '门锁类型：WIFI_LOCK / BLE_LOCK / LORA_LOCK / CAT1_LOCK',
  `ventor`           VARCHAR(64)     NULL     COMMENT '厂商',
  `org_id`           BIGINT UNSIGNED NULL     COMMENT '归属组织',
  `space_id`         BIGINT UNSIGNED NULL     COMMENT '安装空间',
  `install_address`  VARCHAR(500)    NULL     COMMENT '安装地址',
  `install_time`     DATETIME(3)     NULL     COMMENT '安装时间',
  `install_user_id`  BIGINT UNSIGNED NULL     COMMENT '安装人',
  `install_images`   VARCHAR(2000)   NULL     COMMENT '安装照片（逗号分隔）',
  -- 状态缓存（来自 IoT 对账）
  `online_status`    TINYINT(1)      NULL     COMMENT '在线状态：1 在线 0 离线（NULL 未获取）',
  `online_time`      DATETIME(3)     NULL     COMMENT '最近在线时间',
  `offline_time`     DATETIME(3)     NULL     COMMENT '最近离线时间',
  `battery`          INT             NULL     COMMENT '电量百分比',
  `battery_time`     DATETIME(3)     NULL     COMMENT '电量采集时间',
  `rssi`             VARCHAR(20)     NULL     COMMENT '信号强度',
  `soft_version`     VARCHAR(64)     NULL     COMMENT '软件版本',
  `hard_version`     VARCHAR(64)     NULL     COMMENT '硬件版本',
  `status_sync_time` DATETIME(3)     NULL     COMMENT '状态最近同步时间（对账任务写入）',
  -- 业务属性
  `is_public`        TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否公有设备',
  `owner_person_id`  BIGINT UNSIGNED NULL     COMMENT '所有者（人员）',
  `admin_person_id`  BIGINT UNSIGNED NULL     COMMENT '管理者（人员）',
  `usable_person_id` BIGINT UNSIGNED NULL     COMMENT '使用者（人员）',
  `agent_code`       VARCHAR(64)     NULL     COMMENT '代理商编码',
  `device_status`    VARCHAR(20)     NOT NULL DEFAULT 'NORMAL' COMMENT '业务状态：NORMAL 正常 / MAINTENANCE 维护 / SCRAPPED 报废 / UNKNOWN 未知',
  `remark`           VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`        VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_device` (`tenant_id`,`device_id`),
  KEY `idx_tenant_mac` (`tenant_id`,`device_mac`),
  KEY `idx_tenant_type` (`tenant_id`,`device_type`,`device_status`),
  KEY `idx_tenant_org` (`tenant_id`,`org_id`),
  KEY `idx_tenant_space` (`tenant_id`,`space_id`),
  KEY `idx_online` (`tenant_id`,`online_status`,`device_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备业务视图（主数据在 IoT 平台，此处存业务属性与状态缓存）';

-- 7.2 换锁/换表记录（对应漳州标"是否换锁"数据来源）
CREATE TABLE `bp_dev_change_log` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `change_type`    VARCHAR(20)     NOT NULL COMMENT '类型：REPLACE 更换 / REMOVE 拆除 / INSTALL 安装',
  `device_type`    VARCHAR(30)     NOT NULL COMMENT '设备类型',
  `space_id`       BIGINT UNSIGNED NULL     COMMENT '空间ID',
  `house_id`       BIGINT UNSIGNED NULL     COMMENT '房源ID',
  `old_device_id`  VARCHAR(64)     NULL     COMMENT '原设备ID',
  `old_device_mac` VARCHAR(64)     NULL     COMMENT '原设备MAC',
  `new_device_id`  VARCHAR(64)     NULL     COMMENT '新设备ID',
  `new_device_mac` VARCHAR(64)     NULL     COMMENT '新设备MAC',
  `reason`         VARCHAR(500)    NULL     COMMENT '更换原因',
  `work_order_no`  VARCHAR(64)     NULL     COMMENT '关联工单号',
  `operate_user_id` BIGINT UNSIGNED NULL    COMMENT '操作人',
  `operate_time`   DATETIME(3)     NOT NULL COMMENT '操作时间',
  `images`         VARCHAR(2000)   NULL     COMMENT '现场照片',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_time` (`tenant_id`,`operate_time`),
  KEY `idx_tenant_space` (`tenant_id`,`space_id`),
  KEY `idx_tenant_mac` (`tenant_id`,`new_device_mac`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='换锁/换表记录（"是否换锁"数据来源）';

-- 7.3 开门记录 ★大表·按月分区
CREATE TABLE `bp_dev_access_record` (
  `id`                 BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`          VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `event_id`           VARCHAR(64)     NOT NULL COMMENT 'IoT 事件ID（幂等去重用，唯一）',
  `device_id`          VARCHAR(64)     NULL     COMMENT '设备ID',
  `lock_id`            VARCHAR(64)     NULL     COMMENT 'IoT 门锁ID',
  `device_mac`         VARCHAR(64)     NULL     COMMENT '设备MAC',
  `space_id`           BIGINT UNSIGNED NULL     COMMENT '空间ID',
  `house_id`           BIGINT UNSIGNED NULL     COMMENT '房源ID',
  `org_id`             BIGINT UNSIGNED NULL     COMMENT '组织ID',
  `open_type`          VARCHAR(10)     NOT NULL COMMENT '开门方式（IoT 字典）：1001-1049，见 IoT 文档',
  `open_type_name`     VARCHAR(64)     NULL     COMMENT '开门方式名称（解析后）',
  `is_trusted`         TINYINT(1)      NULL     COMMENT '是否可信开门方式：1 可信 0 不可信（用于"不可信占比"预警）',
  `person_id`          BIGINT UNSIGNED NULL     COMMENT '开门人（人员ID，解析后）',
  `target_user_mobile` VARCHAR(64)     NULL     COMMENT '开门用户手机号（IoT 原样）',
  `open_time`          DATETIME(3)     NOT NULL COMMENT '开门时间',
  `source`             VARCHAR(20)     NOT NULL COMMENT '来源：CALLBACK 回调 / PULL 拉取补齐',
  `is_abnormal`        TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否异常（挟持/试错等）',
  `abnormal_type`      VARCHAR(30)     NULL     COMMENT '异常类型：DURESS 挟持 / RETRY 试错 / OFFHOURS 非授权时段 / OTHER',
  `create_time`        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`,`open_time`),
  UNIQUE KEY `uk_tenant_event` (`tenant_id`,`event_id`,`open_time`),
  KEY `idx_tenant_time` (`tenant_id`,`open_time`),
  KEY `idx_tenant_person_time` (`tenant_id`,`person_id`,`open_time`),
  KEY `idx_tenant_house_time` (`tenant_id`,`house_id`,`open_time`),
  KEY `idx_tenant_device_time` (`tenant_id`,`device_id`,`open_time`),
  KEY `idx_tenant_opentype_time` (`tenant_id`,`open_type`,`open_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开门记录（大表，按月分区）'
PARTITION BY RANGE (TO_DAYS(`open_time`)) (
  PARTITION p202610 VALUES LESS THAN (TO_DAYS('2026-11-01')),
  PARTITION p202611 VALUES LESS THAN (TO_DAYS('2026-12-01')),
  PARTITION p202612 VALUES LESS THAN (TO_DAYS('2027-01-01')),
  PARTITION p202701 VALUES LESS THAN (TO_DAYS('2027-02-01')),
  PARTITION p202702 VALUES LESS THAN (TO_DAYS('2027-03-01')),
  PARTITION p202703 VALUES LESS THAN (TO_DAYS('2027-04-01')),
  PARTITION pmax    VALUES LESS THAN MAXVALUE
);
-- 【运维要求】每月 25 日由定时任务自动 ADD PARTITION，并归档 12 个月前的分区
-- 【注意】分区表的主键必须包含分区键，故 PK 为 (id, open_time)

-- 7.4 设备告警记录
CREATE TABLE `bp_dev_device_alert` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `alert_no`      VARCHAR(64)     NOT NULL COMMENT '告警编号',
  `device_id`     VARCHAR(64)     NULL     COMMENT '设备ID',
  `device_mac`    VARCHAR(64)     NULL     COMMENT '设备MAC',
  `device_type`   VARCHAR(30)     NULL     COMMENT '设备类型',
  `space_id`      BIGINT UNSIGNED NULL     COMMENT '空间ID',
  `house_id`      BIGINT UNSIGNED NULL     COMMENT '房源ID',
  `org_id`        BIGINT UNSIGNED NULL     COMMENT '组织ID',
  `alert_type`    VARCHAR(40)     NOT NULL COMMENT '告警类型：LOW_BATTERY 低电量 / OFFLINE 离线 / TAMPER 防拆 / FAULT 故障 / NETWORK 网络异常 / OTHER',
  `alert_level`   VARCHAR(20)     NOT NULL DEFAULT 'NORMAL' COMMENT '级别：URGENT 紧急 / IMPORTANT 重要 / NORMAL 一般',
  `alert_content` VARCHAR(1000)   NULL     COMMENT '告警内容',
  `alert_time`    DATETIME(3)     NOT NULL COMMENT '告警时间',
  `alert_value`   VARCHAR(128)    NULL     COMMENT '告警值（如电量 10%）',
  `source`        VARCHAR(20)     NOT NULL DEFAULT 'PULL' COMMENT '来源：CALLBACK / PULL / DEVICE',
  `handle_status` VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '处理状态：PENDING 待处理 / HANDLING 处理中 / HANDLED 已处理 / IGNORED 已忽略',
  `handle_time`   DATETIME(3)     NULL COMMENT '处置时间',
  `handle_user_id` BIGINT UNSIGNED NULL COMMENT '处置人ID',
  `handle_remark` VARCHAR(500)    NULL COMMENT '处置备注',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_alertno` (`tenant_id`,`alert_no`),
  KEY `idx_tenant_time` (`tenant_id`,`alert_time`),
  KEY `idx_tenant_type_status` (`tenant_id`,`alert_type`,`handle_status`),
  KEY `idx_tenant_device` (`tenant_id`,`device_id`,`alert_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备告警记录';

-- 7.5 设备在线率统计（考核数据来源，必须持久化）
CREATE TABLE `bp_dev_online_stat` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `org_id`          BIGINT UNSIGNED NULL     COMMENT '组织/小区',
  `stat_date`       DATE            NOT NULL COMMENT '统计日期',
  `stat_period`     VARCHAR(20)     NOT NULL COMMENT '考核周期标识（如 2026-H1 / 2026-Q1）',
  `device_type`     VARCHAR(30)     NOT NULL DEFAULT 'LOCK' COMMENT '设备类型',
  `total_count`     INT             NOT NULL DEFAULT 0 COMMENT '总安装数',
  `online_count`    INT             NOT NULL DEFAULT 0 COMMENT '在线数',
  `offline_count`   INT             NOT NULL DEFAULT 0 COMMENT '离线数',
  `online_rate`     DECIMAL(6,4)    NOT NULL DEFAULT 0 COMMENT '在线率（0-1）',
  `sample_count`    INT             NOT NULL DEFAULT 0 COMMENT '对账采样次数',
  `stat_source`     VARCHAR(20)     NOT NULL DEFAULT 'RECONCILE' COMMENT '来源：RECONCILE 对账 / SAMPLE 抽样',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_org_date_type` (`tenant_id`,`org_id`,`stat_date`,`device_type`,`stat_period`),
  KEY `idx_tenant_period` (`tenant_id`,`stat_period`,`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备在线率统计（考核数据，可导出）';

-- 7.6 IoT 接口调用日志
CREATE TABLE `bp_dev_iot_call_log` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `trace_id`       VARCHAR(64)     NULL     COMMENT '链路追踪ID',
  `api_name`       VARCHAR(64)     NOT NULL COMMENT '接口名（如 AUTH_ACTION / GET_OPEN_RECORD / GET_ACCESS_TOKEN）',
  `api_url`        VARCHAR(255)    NULL     COMMENT '接口URL',
  `request_no`     VARCHAR(64)     NULL     COMMENT '请求流水号',
  `biz_type`       VARCHAR(30)     NULL     COMMENT '业务类型：GRANT / REVOKE / QUERY_RECORD / RECONCILE / VERIFY',
  `biz_id`         BIGINT UNSIGNED NULL     COMMENT '业务单据ID',
  `request_body`   TEXT            NULL     COMMENT '请求体（脱敏）',
  `response_body`  TEXT            NULL     COMMENT '响应体（脱敏）',
  `http_status`    INT             NULL     COMMENT 'HTTP 状态码',
  `biz_code`       VARCHAR(40)     NULL     COMMENT '业务返回码（如 status=1）',
  `error_code`     VARCHAR(40)     NULL     COMMENT '错误码（IoT 错误码）',
  `error_msg`      VARCHAR(500)    NULL     COMMENT '错误信息',
  `success_flag`   TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否成功',
  `duration_ms`    INT             NULL     COMMENT '耗时（毫秒）',
  `retry_count`    INT             NOT NULL DEFAULT 0 COMMENT '重试次数',
  `call_time`      DATETIME(3)     NOT NULL COMMENT '调用时间',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_time` (`tenant_id`,`call_time`),
  KEY `idx_tenant_api` (`tenant_id`,`api_name`,`success_flag`),
  KEY `idx_trace` (`trace_id`),
  KEY `idx_biz` (`tenant_id`,`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IoT 接口调用日志（排查与限流分析）';

-- 7.7 回调接收日志（幂等统计）
CREATE TABLE `bp_dev_callback_log` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NULL     COMMENT '租户ID（回调可能无法立即确定租户）',
  `msg_type`      VARCHAR(20)     NOT NULL COMMENT '消息类型：1 开门记录事件回调',
  `event_id`      VARCHAR(64)     NOT NULL COMMENT '事件ID',
  `raw_body`      TEXT            NULL     COMMENT '原始报文',
  `source_ip`     VARCHAR(64)     NULL     COMMENT '来源IP',
  `is_duplicate`  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否重复（幂等命中）',
  `process_status` VARCHAR(20)    NOT NULL DEFAULT 'RECEIVED' COMMENT '处理状态：RECEIVED / PROCESSED / FAILED / IGNORED',
  `error_msg`     VARCHAR(500)    NULL COMMENT '错误信息',
  `receive_time`  DATETIME(3)     NOT NULL COMMENT '接收时间',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_event` (`event_id`),
  KEY `idx_time` (`receive_time`),
  KEY `idx_dup` (`is_duplicate`,`receive_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回调接收日志（含幂等命中统计）';

-- 7.8 对账任务水位（断点续跑）
CREATE TABLE `bp_dev_reconcile_watermark` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `task_type`       VARCHAR(30)     NOT NULL COMMENT '任务类型：ACCESS_RECORD 通行记录 / DEVICE_STATUS 设备状态 / GRANT 授权 / ALERT 告警',
  `shard_no`        INT             NOT NULL DEFAULT 0 COMMENT '分片号',
  `shard_total`     INT             NOT NULL DEFAULT 1 COMMENT '总分片数',
  `last_watermark`  VARCHAR(128)    NULL     COMMENT '上次成功水位（时间戳或ID）',
  `last_run_time`   DATETIME(3)     NULL     COMMENT '上次执行时间',
  `last_result`     VARCHAR(20)     NULL     COMMENT '上次结果：SUCCESS / PARTIAL / FAILED',
  `last_error`      VARCHAR(1000)   NULL     COMMENT '上次错误',
  `diff_count`      INT             NOT NULL DEFAULT 0 COMMENT '累计差异数',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_task_shard` (`tenant_id`,`task_type`,`shard_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对账任务水位（断点续跑）';

-- 7.9 核心功能可用率探针记录（对接漳州标一票否决考核）
CREATE TABLE `bp_dev_availability_probe` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `probe_type`    VARCHAR(40)     NOT NULL COMMENT '探针类型：FACE_VERIFY 人脸核验 / REMOTE_UNLOCK 远程控锁 / ALERT_UPLOAD 报警上传',
  `probe_time`    DATETIME(3)     NOT NULL COMMENT '探测时间',
  `success_flag`  TINYINT(1)      NOT NULL COMMENT '是否成功',
  `duration_ms`   INT             NULL     COMMENT '耗时（毫秒）',
  `error_msg`     VARCHAR(500)    NULL     COMMENT '失败原因',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_type_time` (`tenant_id`,`probe_type`,`probe_time`),
  KEY `idx_tenant_fail` (`tenant_id`,`probe_type`,`success_flag`,`probe_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='核心功能可用率探针记录（一票否决考核依据）';


-- =====================================================================
--  BC-08  告警与工单（ops）
-- =====================================================================

-- 8.1 告警规则（业务规则，与 bp_rule_rule 互补：此处为预警专用视图）
CREATE TABLE `bp_ops_alert_rule` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `rule_code`       VARCHAR(64)     NOT NULL COMMENT '规则编码',
  `rule_name`       VARCHAR(128)    NOT NULL COMMENT '规则名称',
  `rule_category`   VARCHAR(30)     NOT NULL COMMENT '规则类别：SAFETY 安全类 / DEVICE 设备类 / BUSINESS 业务类 / VIOLATION 违规类',
  `rule_type`       VARCHAR(30)     NOT NULL COMMENT '规则类型：EVENT_MATCH 事件匹配 / TIME_WINDOW 时间窗统计 / RATIO 比例阈值 / DEVICE_STATUS 设备状态 / COMBO 组合判别',
  `trigger_event`   VARCHAR(64)     NULL     COMMENT '触发事件（如 access.record / device.status）',
  `condition_expr`  TEXT            NULL     COMMENT '条件表达式（SpEL/Aviator）',
  `threshold_json`  JSON            NULL     COMMENT '阈值配置（多阈值、时间窗）',
  `severity`        VARCHAR(20)     NOT NULL DEFAULT 'NORMAL' COMMENT '级别：URGENT / IMPORTANT / NORMAL',
  `alert_actions`   JSON            NULL     COMMENT '动作列表：NOTIFY 通知 / WORKORDER 生成工单 / FREEZE 冻结权限 / TAG 打标',
  `notify_channels` VARCHAR(128)    NULL     COMMENT '通知渠道（逗号分隔）：SMS / WECHAT / APP / INNER / PLATFORM',
  `notify_receivers` VARCHAR(500)   NULL     COMMENT '通知对象（角色/人员）',
  `scope_org_ids`   VARCHAR(1000)   NULL     COMMENT '适用范围组织（NULL 全部）',
  `silence_minutes` INT             NOT NULL DEFAULT 0 COMMENT '静默期（分钟内同对象不重复告警）',
  `escalate_minutes` INT            NULL     COMMENT '未处置升级时限（分钟）',
  `escalate_to`     VARCHAR(500)    NULL     COMMENT '升级通知对象',
  `priority`        INT             NOT NULL DEFAULT 0 COMMENT '优先级',
  `rule_status`     VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_rulecode` (`tenant_id`,`rule_code`,`is_deleted`),
  KEY `idx_tenant_category` (`tenant_id`,`rule_category`,`rule_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警规则（可配置规则引擎，支撑"预设规则条件、自设阈值"）';

-- 8.2 告警事件（业务告警，区别于设备告警）
CREATE TABLE `bp_ops_alert` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `alert_no`       VARCHAR(64)     NOT NULL COMMENT '告警编号',
  `rule_id`        BIGINT UNSIGNED NULL     COMMENT '命中规则ID',
  `rule_code`      VARCHAR(64)     NULL     COMMENT '命中规则编码',
  `alert_category` VARCHAR(30)     NOT NULL COMMENT '类别：SAFETY / DEVICE / BUSINESS / VIOLATION',
  `alert_type`     VARCHAR(40)     NOT NULL COMMENT '类型：SUBLEASE 转租转借 / IDLE 长期闲置 / CONTRACT_EXPIRE 合同到期 / DEVICE_OFFLINE 设备离线 / LOW_BATTERY 低电量 / TAMPER 暴力拆卸 / UNTRUSTED_RATIO 不可信开门占比 / NON_CONTRACT_OPEN 非合同人开门 / NO_OPEN_LONG 长期未开门 / ARREARS 欠费 / OTHER',
  `alert_level`    VARCHAR(20)     NOT NULL DEFAULT 'NORMAL' COMMENT '级别：URGENT / IMPORTANT / NORMAL',
  `alert_title`    VARCHAR(255)    NOT NULL COMMENT '告警标题',
  `alert_content`  VARCHAR(2000)   NULL     COMMENT '告警内容',
  `alert_value`    VARCHAR(128)    NULL     COMMENT '触发值（如占比 25%）',
  `threshold_value` VARCHAR(128)   NULL     COMMENT '阈值快照',
  -- 关联对象
  `org_id`         BIGINT UNSIGNED NULL     COMMENT '组织',
  `space_id`       BIGINT UNSIGNED NULL     COMMENT '空间',
  `house_id`       BIGINT UNSIGNED NULL     COMMENT '房源',
  `person_id`      BIGINT UNSIGNED NULL     COMMENT '关联人员',
  `device_id`      VARCHAR(64)     NULL     COMMENT '关联设备',
  `contract_id`    BIGINT UNSIGNED NULL     COMMENT '关联合同',
  `related_ids`    VARCHAR(1000)   NULL     COMMENT '关联明细ID（如命中记录ID列表）',
  -- 处置
  `alert_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待处理 / HANDLING 处理中 / HANDLED 已闭环 / IGNORED 误报忽略 / ESCALATED 已升级',
  `handle_user_id` BIGINT UNSIGNED NULL     COMMENT '处置人',
  `handle_time`    DATETIME(3)     NULL     COMMENT '处置时间',
  `handle_action`  VARCHAR(500)    NULL     COMMENT '处置动作',
  `handle_result`  VARCHAR(1000)   NULL     COMMENT '处置结果',
  `workorder_id`   BIGINT UNSIGNED NULL     COMMENT '关联工单ID',
  `escalate_time`  DATETIME(3)     NULL     COMMENT '升级时间',
  `alert_time`     DATETIME(3)     NOT NULL COMMENT '告警时间',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_alertno` (`tenant_id`,`alert_no`),
  KEY `idx_tenant_time` (`tenant_id`,`alert_time`),
  KEY `idx_tenant_type_status` (`tenant_id`,`alert_type`,`alert_status`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`,`alert_status`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_status_level` (`tenant_id`,`alert_status`,`alert_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警事件（统一告警中心）';

-- 8.3 告警通知记录
CREATE TABLE `bp_ops_alert_notify` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `alert_id`    BIGINT UNSIGNED NOT NULL COMMENT '告警ID',
  `channel`     VARCHAR(20)     NOT NULL COMMENT '渠道：SMS / WECHAT / APP / INNER / PLATFORM',
  `receiver_type` VARCHAR(20)   NULL     COMMENT '接收者类型：USER 用户 / ROLE 角色 / PERSON 人员 / EXTERNAL 外部号码',
  `receiver_id` VARCHAR(64)     NULL     COMMENT '接收者标识',
  `receiver_addr` VARCHAR(128)  NULL     COMMENT '接收地址（手机号/openid）',
  `send_status` VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING / SUCCESS / FAILED',
  `send_time`   DATETIME(3)     NULL COMMENT '发送时间',
  `fail_reason` VARCHAR(500)    NULL COMMENT '失败原因',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_alert` (`alert_id`),
  KEY `idx_tenant_status` (`tenant_id`,`send_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警通知记录';

-- 8.4 工单
CREATE TABLE `bp_ops_workorder` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `workorder_no`     VARCHAR(64)     NOT NULL COMMENT '工单号',
  `order_type`       VARCHAR(30)     NOT NULL COMMENT '工单类型：REPAIR 报修 / INSPECT 巡检 / INSTALL 安装 / MAINTAIN 维护 / COMPLAINT 投诉 / CONSULT 咨询 / ALERT 告警处置 / VISIT 走访',
  `order_source`     VARCHAR(30)     NOT NULL COMMENT '来源：TENANT_APP 租户端 / MINIAPP 小程序 / STAFF 员工 / ALERT 告警转 / PHONE 电话 / WALKIN 现场 / IMPORT 导入',
  `org_id`           BIGINT UNSIGNED NULL     COMMENT '所属组织',
  `space_id`         BIGINT UNSIGNED NULL     COMMENT '关联空间',
  `house_id`         BIGINT UNSIGNED NULL     COMMENT '关联房源',
  `device_id`        VARCHAR(64)     NULL     COMMENT '关联设备',
  `device_type`      VARCHAR(30)     NULL     COMMENT '设备类型',
  `person_id`        BIGINT UNSIGNED NULL     COMMENT '报修人/诉求人',
  `reporter_name`    VARCHAR(64)     NULL     COMMENT '报修人姓名',
  `reporter_phone`   VARCHAR(64)     NULL     COMMENT '报修人手机号',
  `order_title`      VARCHAR(255)    NOT NULL COMMENT '工单标题',
  `order_content`    VARCHAR(2000)   NULL     COMMENT '问题描述',
  `order_address`    VARCHAR(500)    NULL     COMMENT '地址',
  `images`           VARCHAR(2000)   NULL     COMMENT '图片（逗号分隔）',
  `videos`           VARCHAR(2000)   NULL     COMMENT '视频（逗号分隔）',
  -- 派单与处理
  `assign_user_id`   BIGINT UNSIGNED NULL     COMMENT '处理人',
  `assign_user_name` VARCHAR(64)     NULL COMMENT '处理人姓名',
  `assign_user_phone` VARCHAR(64)    NULL     COMMENT '维修人员手机号',
  `assign_time`      DATETIME(3)     NULL     COMMENT '派单时间',
  `accept_time`      DATETIME(3)     NULL     COMMENT '接单时间',
  `arrive_time`      DATETIME(3)     NULL     COMMENT '上门时间',
  `finish_time`      DATETIME(3)     NULL     COMMENT '完工时间',
  `close_time`       DATETIME(3)     NULL     COMMENT '闭环时间（考核用：闭环时间-报修时间）',
  -- SLA
  `sla_response_minutes` INT         NULL     COMMENT '响应时限（分钟）',
  `sla_finish_minutes`   INT         NULL     COMMENT '完工时限（分钟）',
  `sla_status`       VARCHAR(20)     NULL     COMMENT 'SLA 状态：ON_TIME 按时 / RESPONSE_TIMEOUT 响应超时 / FINISH_TIMEOUT 完工超时',
  -- 换件（对应考核"是否换锁"）
  `is_device_changed` TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否更换设备（是否换锁）',
  `new_device_mac`   VARCHAR(64)     NULL     COMMENT '新设备MAC',
  `change_log_id`    BIGINT UNSIGNED NULL     COMMENT '换锁记录ID',
  -- 结果
  `order_status`     VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待派单 / ASSIGNED 已派单 / ACCEPTED 已接单 / PROCESSING 处理中 / FINISHED 已完工 / CLOSED 已闭环 / CANCELLED 已取消 / REJECTED 已驳回',
  `handle_result`    VARCHAR(1000)   NULL     COMMENT '处理结果',
  `is_warranty`      TINYINT(1)      NULL     COMMENT '是否在保（过保标识）',
  `evaluate_score`   INT             NULL     COMMENT '评价分数（1-5）',
  `evaluate_content` VARCHAR(500)    NULL     COMMENT '评价内容',
  `evaluate_time`    DATETIME(3)     NULL COMMENT '评价时间',
  `cost_amount`      DECIMAL(14,2)   NULL     COMMENT '费用金额',
  `remark`           VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`        VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_orderno` (`tenant_id`,`workorder_no`),
  KEY `idx_tenant_status` (`tenant_id`,`order_status`,`create_time`),
  KEY `idx_tenant_type` (`tenant_id`,`order_type`,`order_status`),
  KEY `idx_tenant_assign` (`tenant_id`,`assign_user_id`,`order_status`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`),
  KEY `idx_tenant_close` (`tenant_id`,`close_time`),
  KEY `idx_sla` (`tenant_id`,`sla_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单（含 SLA、闭环时间、是否换锁）';

-- 8.5 工单流转记录
CREATE TABLE `bp_ops_workorder_log` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `workorder_id` BIGINT UNSIGNED NOT NULL COMMENT '工单ID',
  `action`       VARCHAR(30)     NOT NULL COMMENT '动作：CREATE 创建 / ASSIGN 派单 / ACCEPT 接单 / TRANSFER 改派 / PROCESS 处理 / FINISH 完工 / CLOSE 闭环 / REJECT 驳回 / CANCEL 取消 / EVALUATE 评价',
  `from_status`  VARCHAR(30)     NULL     COMMENT '原状态',
  `to_status`    VARCHAR(30)     NULL     COMMENT '新状态',
  `operator_id`  BIGINT UNSIGNED NULL COMMENT '操作人ID',
  `operator_name` VARCHAR(64)    NULL COMMENT '操作人姓名',
  `content`      VARCHAR(1000)   NULL     COMMENT '处理说明',
  `images`       VARCHAR(2000)   NULL     COMMENT '图片',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_workorder` (`workorder_id`),
  KEY `idx_tenant_time` (`tenant_id`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单流转记录（全留痕）';

-- 8.6 巡房 / 入户走访（区别于"智慧巡更"）
CREATE TABLE `bp_ops_house_visit` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `visit_no`       VARCHAR(64)     NOT NULL COMMENT '走访单号',
  `visit_type`     VARCHAR(30)     NOT NULL COMMENT '类型：ROUTINE 例行巡房 / VERIFY 使用情况核查 / COMPLAINT 投诉核查 / ALERT 预警核查 / VACANCY 空置核查',
  `org_id`         BIGINT UNSIGNED NULL     COMMENT '组织',
  `space_id`       BIGINT UNSIGNED NULL     COMMENT '空间',
  `house_id`       BIGINT UNSIGNED NULL     COMMENT '房源',
  `person_id`      BIGINT UNSIGNED NULL     COMMENT '被访人',
  `plan_date`      DATE            NULL     COMMENT '计划日期',
  `actual_date`    DATE            NULL     COMMENT '实际走访日期',
  `visit_user_id`  BIGINT UNSIGNED NULL     COMMENT '走访人',
  `visit_user_name` VARCHAR(64)    NULL COMMENT '走访人姓名',
  `trigger_reason` VARCHAR(500)    NULL     COMMENT '触发原因（如系统预警"长期未开门"）',
  `alert_id`       BIGINT UNSIGNED NULL     COMMENT '关联预警ID',
  -- 核查结果
  `is_occupied`    TINYINT(1)      NULL     COMMENT '是否实际有人居住',
  `actual_residents` INT           NULL     COMMENT '实际居住人数',
  `match_result`   VARCHAR(30)     NULL     COMMENT '人房匹配结果：MATCH 一致 / MISMATCH 不一致 / UNKNOWN 无法确认',
  `findings`       VARCHAR(2000)   NULL     COMMENT '发现情况',
  `is_sublease`    TINYINT(1)      NULL     COMMENT '是否发现转租转借',
  `is_idle`        TINYINT(1)      NULL     COMMENT '是否发现闲置',
  `is_illegal_use` TINYINT(1)      NULL     COMMENT '是否违规使用',
  `images`         VARCHAR(2000)   NULL     COMMENT '现场照片',
  `location`       VARCHAR(128)    NULL     COMMENT '签到定位',
  `visit_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待走访 / DONE 已完成 / REFUSED 拒访 / ABSENT 无人 / CANCELLED 已取消',
  `next_action`    VARCHAR(500)    NULL     COMMENT '后续处置建议',
  `workorder_id`   BIGINT UNSIGNED NULL     COMMENT '转工单ID',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_visitno` (`tenant_id`,`visit_no`),
  KEY `idx_tenant_status_date` (`tenant_id`,`visit_status`,`plan_date`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`),
  KEY `idx_tenant_user` (`tenant_id`,`visit_user_id`),
  KEY `idx_match` (`tenant_id`,`match_result`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='巡房/入户走访（替代人工入户走访）';

-- 8.7 自动巡查任务与结果
CREATE TABLE `bp_ops_auto_inspection` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `inspection_no`   VARCHAR(64)     NOT NULL COMMENT '巡查编号',
  `inspection_date` DATE            NOT NULL COMMENT '巡查日期',
  `org_id`          BIGINT UNSIGNED NULL     COMMENT '组织',
  `inspection_type` VARCHAR(30)     NOT NULL COMMENT '类型：DAILY 每日自动巡查 / DEVICE 设备状态巡查 / IDLE 闲置判别 / DAILY_OPEN 开门统计',
  `total_count`     INT             NOT NULL DEFAULT 0 COMMENT '巡查对象数',
  `normal_count`    INT             NOT NULL DEFAULT 0 COMMENT '正常数',
  `abnormal_count`  INT             NOT NULL DEFAULT 0 COMMENT '异常数',
  `abnormal_detail` JSON            NULL     COMMENT '异常明细摘要',
  `alert_count`     INT             NOT NULL DEFAULT 0 COMMENT '生成告警数',
  `visit_count`     INT             NOT NULL DEFAULT 0 COMMENT '生成走访任务数',
  `inspection_status` VARCHAR(20)   NOT NULL DEFAULT 'DONE' COMMENT '状态：RUNNING / DONE / FAILED',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_insno` (`tenant_id`,`inspection_no`),
  KEY `idx_tenant_date` (`tenant_id`,`inspection_date`,`inspection_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='自动巡查任务与结果（7×24 无人化巡查）';

-- 8.8 投诉建议
CREATE TABLE `bp_ops_complaint` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `complaint_no`    VARCHAR(64)     NOT NULL COMMENT '单号',
  `complaint_type`  VARCHAR(30)     NOT NULL COMMENT '类型：COMPLAINT 投诉 / SUGGEST 建议 / CONSULT 咨询 / PRAISE 表扬',
  `source`          VARCHAR(30)     NOT NULL COMMENT '来源：MINIAPP / APP / PHONE / WALKIN / OTHER',
  `org_id`          BIGINT UNSIGNED NULL COMMENT '组织ID',
  `person_id`       BIGINT UNSIGNED NULL     COMMENT '提交人',
  `submitter_name`  VARCHAR(64)     NULL COMMENT '提交人姓名',
  `submitter_phone` VARCHAR(64)     NULL COMMENT '提交人手机号',
  `title`           VARCHAR(255)    NULL COMMENT '标题',
  `content`         VARCHAR(2000)   NULL COMMENT '内容',
  `images`          VARCHAR(2000)   NULL COMMENT '图片URL（逗号分隔）',
  `workorder_id`    BIGINT UNSIGNED NULL     COMMENT '转工单ID',
  `handle_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING / HANDLING / HANDLED / CLOSED',
  `handle_user_id`  BIGINT UNSIGNED NULL COMMENT '处置人ID',
  `handle_time`     DATETIME(3)     NULL COMMENT '处置时间',
  `handle_result`   VARCHAR(1000)   NULL COMMENT '处置/处理结果',
  `satisfaction`    INT             NULL     COMMENT '满意度（1-5）',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_complaintno` (`tenant_id`,`complaint_no`),
  KEY `idx_tenant_status` (`tenant_id`,`handle_status`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投诉建议';

-- ---------------------------------------------------------------------
-- P4 完成：BC-07 设备与通信（9 表，含 1 分区表）、BC-08 告警与工单（8 表）= 17 表
-- 累计：76 表
-- ---------------------------------------------------------------------
