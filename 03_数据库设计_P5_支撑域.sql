-- =====================================================================
--  云门道业务平台 —— 数据库设计（第三轮）
--  第 5 部分：支撑域
--    flow 流程引擎(5) / rule 规则引擎(3) / msg 消息通知(4) / rpt 报表与大屏(5)
--    gov  监管报送与备案(4) / open 开放平台(5) / sys 系统与日志(9)
--  合计：35 表
--  目标库：MySQL 8.0+  /  InnoDB  /  utf8mb4
-- =====================================================================

SET NAMES utf8mb4;
USE `bp_platform`;


-- =====================================================================
--  流程引擎（flow）—— 内核级独立模块
--  说明：自研轻量流程引擎，不引入 Activiti/Flowable（私有化资源与源码交付考虑）
-- =====================================================================

-- F1 流程定义
CREATE TABLE `bp_flow_definition` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `flow_code`     VARCHAR(64)     NOT NULL COMMENT '流程编码（如 QUALIFY_REVIEW 资格审核）',
  `flow_name`     VARCHAR(128)    NOT NULL COMMENT '流程名称',
  `flow_category` VARCHAR(30)     NOT NULL COMMENT '分类：QUALIFY 资格审核 / ALLOCATION 配租 / CONTRACT 合同 / ARREARS 欠费 / TERMINATION 退租 / REFUND 退款 / REPAIR 报修 / OTHER',
  `scenario`      VARCHAR(30)     NULL     COMMENT '所属场景包（NULL 内核通用）',
  `flow_version`  INT             NOT NULL DEFAULT 1 COMMENT '版本',
  `flow_status`   VARCHAR(20)     NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT 草稿 / PUBLISHED 已发布 / DISABLED 已停用',
  `description`   VARCHAR(500)    NULL COMMENT '说明',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_flowcode_ver` (`tenant_id`,`flow_code`,`flow_version`),
  KEY `idx_tenant_category` (`tenant_id`,`flow_category`,`flow_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程定义（版本化）';

-- F2 流程节点
CREATE TABLE `bp_flow_node` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `flow_def_id`   BIGINT UNSIGNED NOT NULL COMMENT '流程定义ID',
  `node_code`     VARCHAR(64)     NOT NULL COMMENT '节点编码',
  `node_name`     VARCHAR(128)    NOT NULL COMMENT '节点名称',
  `node_type`     VARCHAR(30)     NOT NULL COMMENT '节点类型：START 开始 / APPROVE 审批 / CONDITION 条件分支 / PARALLEL 并行会签 / COUNTERSIGN 会签 / CC 抄送 / AUTO 自动处理 / END 结束',
  `sort_no`       INT             NOT NULL DEFAULT 0 COMMENT '顺序号',
  `approve_mode`  VARCHAR(30)     NULL     COMMENT '审批模式：ANY 任一人通过 / ALL 全部通过 / MAJORITY 多数通过',
  `approver_type` VARCHAR(30)     NULL     COMMENT '审批人类型：USER 指定人 / ROLE 角色 / ORG_LEADER 组织负责人 / UPPER 上级 / INITIATOR_LEADER 发起人主管',
  `approver_ids`  VARCHAR(1000)   NULL     COMMENT '审批人标识列表（逗号分隔）',
  `timeout_hours` INT             NULL     COMMENT '超时时限（小时）',
  `timeout_action` VARCHAR(30)    NULL     COMMENT '超时动作：REMIND 提醒 / AUTO_PASS 自动通过 / ESCALATE 升级',
  `condition_expr` TEXT           NULL     COMMENT '条件表达式（CONDITION 类型）',
  `form_perm`     JSON            NULL     COMMENT '表单字段权限（可编辑/只读/隐藏）',
  `next_node_code` VARCHAR(255)   NULL     COMMENT '下一节点编码（多个逗号分隔）',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_flowdef` (`flow_def_id`,`sort_no`),
  UNIQUE KEY `uk_flow_node` (`flow_def_id`,`node_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程节点';

-- F3 流程实例
CREATE TABLE `bp_flow_instance` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `instance_no`    VARCHAR(64)     NOT NULL COMMENT '实例编号',
  `flow_def_id`    BIGINT UNSIGNED NOT NULL COMMENT '流程定义ID',
  `flow_code`      VARCHAR(64)     NOT NULL COMMENT '流程编码',
  `biz_type`       VARCHAR(40)     NOT NULL COMMENT '业务类型（如 APPLICATION / TERMINATION / REFUND）',
  `biz_id`         BIGINT UNSIGNED NOT NULL COMMENT '业务单据ID',
  `biz_no`         VARCHAR(64)     NULL     COMMENT '业务单据号',
  `title`          VARCHAR(255)    NULL     COMMENT '流程标题',
  `initiator_id`   BIGINT UNSIGNED NULL     COMMENT '发起人',
  `initiator_name` VARCHAR(64)     NULL COMMENT '发起人姓名',
  `current_node`   VARCHAR(64)     NULL     COMMENT '当前节点编码',
  `instance_status` VARCHAR(20)    NOT NULL DEFAULT 'RUNNING' COMMENT '状态：RUNNING 进行中 / APPROVED 已通过 / REJECTED 已驳回 / CANCELLED 已撤销 / TERMINATED 已终止',
  `start_time`     DATETIME(3)     NOT NULL COMMENT '开始时间',
  `end_time`       DATETIME(3)     NULL     COMMENT '结束时间',
  `duration_hours` DECIMAL(10,2)   NULL     COMMENT '耗时（小时）',
  `biz_data`       JSON            NULL     COMMENT '业务数据快照',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_insno` (`tenant_id`,`instance_no`),
  KEY `idx_tenant_biz` (`tenant_id`,`biz_type`,`biz_id`),
  KEY `idx_tenant_status` (`tenant_id`,`instance_status`,`start_time`),
  KEY `idx_initiator` (`tenant_id`,`initiator_id`,`instance_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程实例';

-- F4 流程任务（待办）
CREATE TABLE `bp_flow_task` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `instance_id`    BIGINT UNSIGNED NOT NULL COMMENT '流程实例ID',
  `node_code`      VARCHAR(64)     NOT NULL COMMENT '节点编码',
  `node_name`      VARCHAR(128)    NULL     COMMENT '节点名称',
  `task_type`      VARCHAR(20)     NOT NULL DEFAULT 'APPROVE' COMMENT '类型：APPROVE 审批 / CC 抄送 / HANDLE 办理',
  `assignee_id`    BIGINT UNSIGNED NULL     COMMENT '办理人',
  `assignee_name`  VARCHAR(64)     NULL COMMENT '办理人姓名',
  `assignee_role`  VARCHAR(64)     NULL     COMMENT '办理角色',
  `task_status`    VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待办 / DONE 已办 / TRANSFERRED 已转办 / CANCELLED 已取消',
  `action`         VARCHAR(20)     NULL     COMMENT '办理动作：PASS 通过 / REJECT 驳回 / SUPPLEMENT 补件 / TRANSFER 转办 / ADD_SIGN 加签',
  `opinion`        VARCHAR(1000)   NULL     COMMENT '办理意见',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `handle_time`    DATETIME(3)     NULL     COMMENT '办理时间',
  `timeout_time`   DATETIME(3)     NULL     COMMENT '超时时间',
  PRIMARY KEY (`id`),
  KEY `idx_instance` (`instance_id`),
  KEY `idx_tenant_assignee` (`tenant_id`,`assignee_id`,`task_status`),
  KEY `idx_tenant_status_time` (`tenant_id`,`task_status`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程任务（待办）';

-- F5 流程流转日志
CREATE TABLE `bp_flow_log` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `instance_id`   BIGINT UNSIGNED NOT NULL COMMENT '流程实例ID',
  `node_code`     VARCHAR(64)     NULL COMMENT '节点编码',
  `action`        VARCHAR(30)     NOT NULL COMMENT '动作：START / PASS / REJECT / SUPPLEMENT / TRANSFER / ADD_SIGN / CC / END / CANCEL / TERMINATE',
  `operator_id`   BIGINT UNSIGNED NULL COMMENT '操作人ID',
  `operator_name` VARCHAR(64)     NULL COMMENT '操作人姓名',
  `opinion`       VARCHAR(1000)   NULL COMMENT '办理意见',
  `attachments`   VARCHAR(2000)   NULL COMMENT '附件URL（逗号分隔）',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_instance` (`instance_id`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程流转日志';


-- =====================================================================
--  规则引擎（rule）—— 预警/资格/计费共用内核
-- =====================================================================

-- R1 规则集
CREATE TABLE `bp_rule_ruleset` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `ruleset_code`  VARCHAR(64)     NOT NULL COMMENT '规则集编码',
  `ruleset_name`  VARCHAR(128)    NOT NULL COMMENT '规则集名称（如"漳州-公租房-资格准入"）',
  `domain`        VARCHAR(30)     NOT NULL COMMENT '领域：ALERT 预警 / QUALIFY 资格 / BILLING 计费',
  `scenario`      VARCHAR(30)     NULL     COMMENT '场景包',
  `security_type` VARCHAR(30)     NULL     COMMENT '保障类型（保障房细分）',
  `org_id`        BIGINT UNSIGNED NULL     COMMENT '适用组织（NULL 全租户）',
  `ruleset_version` INT           NOT NULL DEFAULT 1 COMMENT '版本',
  `effective_start` DATETIME(3)   NULL COMMENT '生效开始时间',
  `effective_end`   DATETIME(3)   NULL COMMENT '生效结束时间',
  `ruleset_status` VARCHAR(20)    NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT 草稿 / PUBLISHED 已发布 / DISABLED 已停用',
  `is_default`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否场景默认规则集',
  `description`   VARCHAR(500)    NULL COMMENT '说明',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_setcode_ver` (`tenant_id`,`ruleset_code`,`ruleset_version`),
  KEY `idx_tenant_domain` (`tenant_id`,`domain`,`ruleset_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='规则集（按租户+场景+领域）';

-- R2 规则
CREATE TABLE `bp_rule_rule` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `ruleset_id`     BIGINT UNSIGNED NOT NULL COMMENT '规则集ID',
  `rule_code`      VARCHAR(64)     NOT NULL COMMENT '规则编码',
  `rule_name`      VARCHAR(128)    NOT NULL COMMENT '规则名称',
  `condition_expr` TEXT            NOT NULL COMMENT '条件表达式（SpEL/Aviator）',
  `threshold_json` JSON            NULL     COMMENT '阈值参数（可配置，对应"自设阈值"要求）',
  `severity`       VARCHAR(20)     NULL     COMMENT '级别（预警用）：URGENT / IMPORTANT / NORMAL',
  `score_expr`     VARCHAR(500)    NULL     COMMENT '打分表达式（资格打分用）',
  `actions_json`   JSON            NULL     COMMENT '动作列表（预警用）',
  `priority`       INT             NOT NULL DEFAULT 0 COMMENT '优先级（数值大者优先）',
  `rule_status`    VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ruleset_rulecode` (`ruleset_id`,`rule_code`),
  KEY `idx_tenant_status` (`tenant_id`,`rule_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='规则（条件+阈值+动作）';

-- R3 规则执行日志（命中与结果，用于误报率分析）
CREATE TABLE `bp_rule_execute_log` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `ruleset_id`   BIGINT UNSIGNED NULL COMMENT '规则集ID',
  `rule_id`      BIGINT UNSIGNED NULL COMMENT '规则ID',
  `rule_code`    VARCHAR(64)     NULL COMMENT '规则编码',
  `domain`       VARCHAR(30)     NOT NULL COMMENT '领域：ALERT / QUALIFY / BILLING',
  `biz_type`     VARCHAR(40)     NULL     COMMENT '触发业务类型',
  `biz_id`       BIGINT UNSIGNED NULL     COMMENT '触发业务ID',
  `hit_flag`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否命中',
  `input_snapshot` JSON          NULL     COMMENT '输入快照',
  `output_snapshot` JSON         NULL     COMMENT '输出快照',
  `action_result` VARCHAR(1000)  NULL     COMMENT '动作执行结果',
  `duration_ms`  INT             NULL     COMMENT '执行耗时',
  `execute_time` DATETIME(3)     NOT NULL COMMENT '执行时间',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_rule_time` (`tenant_id`,`rule_id`,`execute_time`),
  KEY `idx_tenant_hit` (`tenant_id`,`domain`,`hit_flag`,`execute_time`),
  KEY `idx_biz` (`tenant_id`,`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='规则执行日志（误报率与效果分析）';


-- =====================================================================
--  消息通知（msg）
-- =====================================================================

-- M1 消息模板
CREATE TABLE `bp_msg_template` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NULL     COMMENT '租户ID（NULL 为系统内置模板）',
  `template_code`  VARCHAR(64)     NOT NULL COMMENT '模板编码',
  `template_name`  VARCHAR(128)    NOT NULL COMMENT '模板名称',
  `channel`        VARCHAR(20)     NOT NULL COMMENT '渠道：SMS / WECHAT / APP_PUSH / INNER / EMAIL / PLATFORM',
  `biz_type`       VARCHAR(40)     NULL     COMMENT '业务类型：CONTRACT_EXPIRE / BILL_DUE / ARREARS / ALERT / VERIFY / WORKORDER / OTHER',
  `title_tpl`      VARCHAR(255)    NULL     COMMENT '标题模板',
  `content_tpl`    TEXT            NOT NULL COMMENT '内容模板（变量占位符 ${xxx}）',
  `variables`      JSON            NULL     COMMENT '变量定义',
  `third_tpl_id`   VARCHAR(128)    NULL     COMMENT '第三方模板ID（微信/短信服务商）',
  `template_status` VARCHAR(20)    NOT NULL DEFAULT 'ENABLED' COMMENT '模板状态：ENABLED / DISABLED',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_tplcode_channel` (`tenant_id`,`template_code`,`channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息模板';

-- M2 消息订阅配置
CREATE TABLE `bp_msg_subscription` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `biz_type`       VARCHAR(40)     NOT NULL COMMENT '业务类型/事件类型',
  `subscriber_type` VARCHAR(20)    NOT NULL COMMENT '订阅者类型：ROLE / USER / PERSON / EXTERNAL',
  `subscriber_id`  VARCHAR(64)     NULL     COMMENT '订阅者标识',
  `channels`       VARCHAR(128)    NOT NULL COMMENT '渠道（逗号分隔）',
  `filter_expr`    VARCHAR(500)    NULL     COMMENT '过滤条件（如仅某组织/某级别）',
  `sub_status`     VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '订阅状态：ENABLED / DISABLED',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_biz` (`tenant_id`,`biz_type`,`sub_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息订阅配置（多维订阅）';

-- M3 消息发送记录 ★大表
CREATE TABLE `bp_msg_send_record` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `message_no`    VARCHAR(64)     NOT NULL COMMENT '消息编号',
  `template_code` VARCHAR(64)     NULL     COMMENT '模板编码',
  `channel`       VARCHAR(20)     NOT NULL COMMENT '渠道',
  `biz_type`      VARCHAR(40)     NULL     COMMENT '业务类型',
  `biz_id`        BIGINT UNSIGNED NULL     COMMENT '业务单据ID',
  `receiver_type` VARCHAR(20)     NULL     COMMENT '接收者类型',
  `receiver_id`   VARCHAR(64)     NULL     COMMENT '接收者ID',
  `receiver_name` VARCHAR(64)     NULL COMMENT '接收者姓名',
  `receiver_addr` VARCHAR(128)    NULL     COMMENT '接收地址（手机号/openid）',
  `title`         VARCHAR(255)    NULL COMMENT '标题',
  `content`       TEXT            NULL     COMMENT '实际发送内容',
  `send_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待发送 / SENDING 发送中 / SUCCESS 成功 / FAILED 失败',
  `retry_count`   INT             NOT NULL DEFAULT 0 COMMENT '重试次数',
  `fail_reason`   VARCHAR(500)    NULL COMMENT '失败原因',
  `third_msg_id`  VARCHAR(128)    NULL     COMMENT '第三方消息ID',
  `plan_time`     DATETIME(3)     NULL     COMMENT '计划发送时间（延迟消息）',
  `send_time`     DATETIME(3)     NULL     COMMENT '实际发送时间',
  `deliver_time`  DATETIME(3)     NULL     COMMENT '到达时间（回执）',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_msgn` (`tenant_id`,`message_no`),
  KEY `idx_tenant_status_plan` (`tenant_id`,`send_status`,`plan_time`),
  KEY `idx_tenant_biz` (`tenant_id`,`biz_type`,`biz_id`),
  KEY `idx_tenant_receiver` (`tenant_id`,`receiver_id`,`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息发送记录';

-- M4 待办事项（站内）
CREATE TABLE `bp_msg_todo` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `user_id`      BIGINT UNSIGNED NOT NULL COMMENT '接收用户',
  `todo_type`    VARCHAR(30)     NOT NULL COMMENT '类型：APPROVE 审批 / HANDLE 办理 / ALERT 告警 / REMIND 提醒 / NOTICE 通知',
  `title`        VARCHAR(255)    NOT NULL COMMENT '标题',
  `content`      VARCHAR(1000)   NULL COMMENT '内容',
  `biz_type`     VARCHAR(40)     NULL COMMENT '业务类型',
  `biz_id`       BIGINT UNSIGNED NULL COMMENT '业务单据ID',
  `link_url`     VARCHAR(500)    NULL     COMMENT '跳转链接',
  `priority`     VARCHAR(20)     NOT NULL DEFAULT 'NORMAL' COMMENT '优先级：URGENT / IMPORTANT / NORMAL',
  `todo_status`  VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 未读 / READ 已读 / DONE 已办',
  `expire_time`  DATETIME(3)     NULL     COMMENT '过期时间',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `read_time`    DATETIME(3)     NULL COMMENT '已读时间',
  `done_time`    DATETIME(3)     NULL COMMENT '办结时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_user_status` (`tenant_id`,`user_id`,`todo_status`,`create_time`),
  KEY `idx_biz` (`tenant_id`,`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='待办事项（站内）';


-- =====================================================================
--  报表与大屏（rpt）
-- =====================================================================

-- T1 指标日汇总
CREATE TABLE `bp_rpt_metric_daily` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `stat_date`     DATE            NOT NULL COMMENT '统计日期',
  `org_id`        BIGINT UNSIGNED NULL     COMMENT '组织（NULL 为租户级）',
  `metric_code`   VARCHAR(64)     NOT NULL COMMENT '指标编码',
  `metric_name`   VARCHAR(128)    NULL     COMMENT '指标名称',
  `metric_value`  DECIMAL(18,4)   NOT NULL DEFAULT 0 COMMENT '指标值',
  `metric_unit`   VARCHAR(20)     NULL     COMMENT '单位',
  `dimension_json` JSON           NULL     COMMENT '维度明细（如房间状态分布）',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_org_date_metric` (`tenant_id`,`org_id`,`stat_date`,`metric_code`),
  KEY `idx_tenant_metric_date` (`tenant_id`,`metric_code`,`stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标日汇总（大屏与报表数据源）';

-- T2 指标小时汇总（当日走势）
CREATE TABLE `bp_rpt_metric_hourly` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `stat_hour`    DATETIME(3)     NOT NULL COMMENT '统计小时（整点）',
  `org_id`       BIGINT UNSIGNED NULL COMMENT '组织ID',
  `metric_code`  VARCHAR(64)     NOT NULL COMMENT '指标编码',
  `metric_value` DECIMAL(18,4)   NOT NULL DEFAULT 0 COMMENT '指标值',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_org_hour_metric` (`tenant_id`,`org_id`,`stat_hour`,`metric_code`),
  KEY `idx_tenant_hour` (`tenant_id`,`stat_hour`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标小时汇总';

-- T3 报表定义
CREATE TABLE `bp_rpt_report_def` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NULL     COMMENT '租户ID（NULL 系统内置）',
  `report_code`   VARCHAR(64)     NOT NULL COMMENT '报表编码',
  `report_name`   VARCHAR(128)    NOT NULL COMMENT '报表名称',
  `report_type`   VARCHAR(30)     NOT NULL COMMENT '类型：HOUSE 房源 / PERSON 人员 / CONTRACT 合同 / FINANCE 财务 / ARREARS 欠费 / SUBSIDY 补贴 / ACCESS 通行 / ALERT 告警 / WORKORDER 工单 / DEVICE 设备',
  `scenario`      VARCHAR(30)     NULL     COMMENT '场景包',
  `query_config`  JSON            NULL     COMMENT '查询配置（字段、条件、排序）',
  `column_config` JSON            NULL     COMMENT '列配置（表头、宽度、格式化）',
  `export_format` VARCHAR(20)     NOT NULL DEFAULT 'EXCEL' COMMENT '导出格式：EXCEL / CSV / PDF',
  `report_status` VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '报表状态：ENABLED / DISABLED',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_reportcode` (`tenant_id`,`report_code`,`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报表定义';

-- T4 导出任务（异步导出，对应漳州标"时间跨度自定义导出"）
CREATE TABLE `bp_rpt_export_task` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `task_no`       VARCHAR(64)     NOT NULL COMMENT '任务号',
  `export_type`   VARCHAR(40)     NOT NULL COMMENT '导出类型：WORKORDER 工单记录 / ONLINE_RATE 在线率 / FAULT_STAT 故障分类 / AVAILABILITY 核心功能可用率 / ALERT 告警记录 / CUSTOM 自定义报表',
  `report_code`   VARCHAR(64)     NULL     COMMENT '报表编码',
  `query_params`  JSON            NULL     COMMENT '查询参数（起止时间等，支持时间跨度自定义）',
  `file_name`     VARCHAR(255)    NULL     COMMENT '文件名',
  `file_url`      VARCHAR(500)    NULL     COMMENT '文件URL',
  `file_size`     BIGINT          NULL     COMMENT '文件大小（字节）',
  `row_count`     INT             NULL     COMMENT '导出行数',
  `task_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 排队 / RUNNING 生成中 / SUCCESS 成功 / FAILED 失败 / EXPIRED 已过期',
  `progress`      INT             NOT NULL DEFAULT 0 COMMENT '进度（0-100）',
  `fail_reason`   VARCHAR(500)    NULL COMMENT '失败原因',
  `expire_time`   DATETIME(3)     NULL     COMMENT '文件过期时间',
  `user_id`       BIGINT UNSIGNED NULL     COMMENT '发起人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `finish_time`   DATETIME(3)     NULL COMMENT '完成时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_taskno` (`tenant_id`,`task_no`),
  KEY `idx_tenant_status` (`tenant_id`,`task_status`,`create_time`),
  KEY `idx_tenant_user` (`tenant_id`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='导出任务（异步，支持时间跨度自定义）';

-- T5 大屏定义
CREATE TABLE `bp_rpt_screen_def` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NULL     COMMENT '租户ID',
  `screen_code`   VARCHAR(64)     NOT NULL COMMENT '大屏编码',
  `screen_name`   VARCHAR(128)    NOT NULL COMMENT '大屏名称',
  `screen_type`   VARCHAR(30)     NOT NULL COMMENT '类型：OVERVIEW 总览 / HOUSE 房源 / PERSON 人员 / DEVICE 设备 / ACCESS 通行 / FINANCE 资金 / ALERT 预警 / PROJECT 项目 / MAP 地图',
  `scenario`      VARCHAR(30)     NULL     COMMENT '场景包',
  `layout_config` JSON            NULL     COMMENT '布局配置（组件、位置、尺寸）',
  `widget_config` JSON            NULL     COMMENT '组件配置（指标、图表类型、数据源）',
  `refresh_seconds` INT           NOT NULL DEFAULT 60 COMMENT '刷新间隔（秒）',
  `screen_status` VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '大屏状态',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_screencode` (`tenant_id`,`screen_code`,`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='大屏定义（可配置布局与组件）';


-- =====================================================================
--  监管报送与备案（gov）★ 竞品校准新增域
-- =====================================================================

-- G1 监管报送任务
CREATE TABLE `bp_gov_report_task` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `task_no`        VARCHAR(64)     NOT NULL COMMENT '任务号',
  `target_system`  VARCHAR(40)     NOT NULL COMMENT '目标系统：PUBLIC_HOUSING 公租房管理信息系统 / POLICE 公安可信身份平台 / HOUSING 住建 / REAL_ESTATE 房管局备案 / STATISTICS 统计上报 / OTHER',
  `report_type`    VARCHAR(40)     NOT NULL COMMENT '报送类型：HOUSE 房源 / TENANT 租户 / STATUS 状态 / CONTRACT 合同 / FINANCE 财务 / ACCESS 通行 / ALERT 告警 / PERSON 人员',
  `report_mode`    VARCHAR(20)     NOT NULL COMMENT '方式：API 接口 / FILE 文件交换 / MANUAL 人工',
  `report_cycle`   VARCHAR(20)     NULL     COMMENT '周期：REALTIME 实时 / DAILY 日 / MONTHLY 月 / QUARTERLY 季 / ONCE 一次性',
  `data_range`     JSON            NULL     COMMENT '数据范围（时间跨度、组织范围，支持自定义）',
  `record_count`   INT             NOT NULL DEFAULT 0 COMMENT '记录数',
  `success_count`  INT             NOT NULL DEFAULT 0 COMMENT '成功数',
  `fail_count`     INT             NOT NULL DEFAULT 0 COMMENT '失败数',
  `file_url`       VARCHAR(500)    NULL     COMMENT '报送文件URL',
  `task_status`    VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待报送 / RUNNING 报送中 / SUCCESS 成功 / PARTIAL 部分成功 / FAILED 失败',
  `fail_detail`    VARCHAR(2000)   NULL     COMMENT '失败明细',
  `report_time`    DATETIME(3)     NULL     COMMENT '报送时间',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_taskno` (`tenant_id`,`task_no`),
  KEY `idx_tenant_target` (`tenant_id`,`target_system`,`task_status`),
  KEY `idx_tenant_time` (`tenant_id`,`report_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监管报送任务（房管局备案/公租房系统/公安平台）';

-- G2 监管报送明细（逐条结果）
CREATE TABLE `bp_gov_report_detail` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `task_id`       BIGINT UNSIGNED NOT NULL COMMENT '报送任务ID',
  `biz_type`      VARCHAR(40)     NOT NULL COMMENT '业务类型',
  `biz_id`        BIGINT UNSIGNED NULL     COMMENT '业务ID',
  `external_id`   VARCHAR(128)    NULL     COMMENT '外部系统ID（回写）',
  `sync_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING / SUCCESS / FAILED / SKIPPED',
  `error_code`    VARCHAR(40)     NULL COMMENT '错误码',
  `error_msg`     VARCHAR(500)    NULL COMMENT '错误信息',
  `request_data`  JSON            NULL     COMMENT '报送数据快照',
  `response_data` JSON            NULL     COMMENT '响应数据',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_task` (`task_id`,`sync_status`),
  KEY `idx_biz` (`tenant_id`,`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监管报送明细';

-- G3 外部系统接口配置
CREATE TABLE `bp_gov_adapter_config` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `adapter_code`   VARCHAR(64)     NOT NULL COMMENT '适配器编码（如 PUBLIC_HOUSING_API / REAL_ESTATE_API）',
  `adapter_name`   VARCHAR(128)    NOT NULL COMMENT '适配器名称',
  `system_type`    VARCHAR(40)     NOT NULL COMMENT '系统类型',
  `protocol`       VARCHAR(20)     NOT NULL DEFAULT 'HTTP' COMMENT '协议：HTTP / WEBSOCKET / FILE / SFTP / DB',
  `endpoint`       VARCHAR(500)    NULL     COMMENT '服务地址',
  `auth_type`      VARCHAR(30)     NULL     COMMENT '鉴权方式：NONE / APPKEY / TOKEN / BASIC / CERT / SIGN',
  `auth_config`    JSON            NULL     COMMENT '鉴权配置（加密存储）',
  `timeout_ms`     INT             NOT NULL DEFAULT 10000 COMMENT '超时（毫秒）',
  `retry_times`    INT             NOT NULL DEFAULT 3 COMMENT '重试次数',
  `qps_limit`      INT             NULL     COMMENT 'QPS 限流',
  `degrade_mode`   VARCHAR(20)     NOT NULL DEFAULT 'RETRY' COMMENT '降级方式：RETRY 重试 / MANUAL 转人工 / FILE 文件交换 / BLOCK 阻断',
  `adapter_status` VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '适配器状态：ENABLED / DISABLED',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_adapter` (`tenant_id`,`adapter_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部系统接口配置（适配器）';

-- G4 适配器调用日志
CREATE TABLE `bp_gov_adapter_log` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `adapter_code`  VARCHAR(64)     NOT NULL COMMENT '适配器编码',
  `trace_id`      VARCHAR(64)     NULL COMMENT '链路追踪ID',
  `biz_type`      VARCHAR(40)     NULL COMMENT '业务类型',
  `biz_id`        BIGINT UNSIGNED NULL COMMENT '业务单据ID',
  `request_body`  TEXT            NULL     COMMENT '请求（脱敏）',
  `response_body` TEXT            NULL     COMMENT '响应（脱敏）',
  `success_flag`  TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否成功：1 是 0 否',
  `error_msg`     VARCHAR(500)    NULL COMMENT '错误信息',
  `duration_ms`   INT             NULL COMMENT '耗时（毫秒）',
  `call_time`     DATETIME(3)     NOT NULL COMMENT '调用时间',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_adapter_time` (`tenant_id`,`adapter_code`,`call_time`),
  KEY `idx_biz` (`tenant_id`,`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='适配器调用日志';


-- =====================================================================
--  开放平台（open）★ 补齐"有接口无管理后台"的缺口
-- =====================================================================

-- O1 开放应用
CREATE TABLE `bp_open_app` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `app_key`         VARCHAR(64)     NOT NULL COMMENT 'AppKey',
  `app_secret`      VARCHAR(256)    NOT NULL COMMENT 'AppSecret（加密存储）',
  `app_name`        VARCHAR(128)    NOT NULL COMMENT '应用名称',
  `app_type`        VARCHAR(30)     NOT NULL DEFAULT 'THIRD_PARTY' COMMENT '类型：THIRD_PARTY 第三方 / INTERNAL 内部 / GOV 政务',
  `owner_org`       VARCHAR(128)    NULL     COMMENT '所属单位',
  `contact_name`    VARCHAR(64)     NULL COMMENT '联系人',
  `contact_phone`   VARCHAR(64)     NULL COMMENT '联系电话',
  `ip_whitelist`    VARCHAR(1000)   NULL     COMMENT 'IP 白名单（逗号分隔）',
  `qps_limit`       INT             NOT NULL DEFAULT 10 COMMENT 'QPS 限流',
  `daily_quota`     INT             NULL     COMMENT '日调用配额',
  `scope_codes`     VARCHAR(2000)   NULL     COMMENT '授权接口范围（逗号分隔）',
  `expire_date`     DATE            NULL     COMMENT '有效期',
  `app_status`      VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED / EXPIRED',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_appkey` (`app_key`),
  KEY `idx_tenant_status` (`tenant_id`,`app_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开放应用（AppKey/AppSecret 管理）';

-- O2 开放接口清单
CREATE TABLE `bp_open_api` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `api_code`      VARCHAR(64)     NOT NULL COMMENT '接口编码',
  `api_name`      VARCHAR(128)    NOT NULL COMMENT '接口名称',
  `api_path`      VARCHAR(255)    NOT NULL COMMENT '接口路径',
  `http_method`   VARCHAR(10)     NOT NULL DEFAULT 'POST' COMMENT 'HTTP 方法',
  `api_group`     VARCHAR(40)     NULL     COMMENT '分组：HOUSE 房源 / PERSON 人员 / CONTRACT 合同 / ACCESS 通行 / ALERT 告警 / DEVICE 设备 / FINANCE 财务',
  `need_auth`     TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否需要鉴权',
  `rate_limit`    INT             NULL     COMMENT '单项限流（QPS）',
  `api_status`    VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '接口状态',
  `description`   VARCHAR(500)    NULL COMMENT '说明',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_api_code` (`api_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开放接口清单';

-- O3 开放调用日志
CREATE TABLE `bp_open_call_log` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `app_key`      VARCHAR(64)     NOT NULL COMMENT '应用标识 AppKey',
  `api_code`     VARCHAR(64)     NULL COMMENT '接口编码',
  `api_path`     VARCHAR(255)    NULL COMMENT '接口路径',
  `request_id`   VARCHAR(64)     NULL COMMENT '请求ID',
  `client_ip`    VARCHAR(64)     NULL COMMENT '客户端IP',
  `request_body` TEXT            NULL     COMMENT '请求（脱敏）',
  `response_code` VARCHAR(40)    NULL COMMENT '响应码',
  `success_flag` TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否成功：1 是 0 否',
  `error_msg`    VARCHAR(500)    NULL COMMENT '错误信息',
  `duration_ms`  INT             NULL COMMENT '耗时（毫秒）',
  `call_time`    DATETIME(3)     NOT NULL COMMENT '调用时间',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_app_time` (`app_key`,`call_time`),
  KEY `idx_api` (`api_code`,`call_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开放调用日志';

-- O4 Webhook 订阅
CREATE TABLE `bp_open_webhook` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `hook_name`     VARCHAR(128)    NOT NULL COMMENT '名称',
  `callback_url`  VARCHAR(500)    NOT NULL COMMENT '回调地址',
  `event_types`   VARCHAR(1000)   NOT NULL COMMENT '订阅事件（逗号分隔）：contract.effective / access.record / alert.raised / bill.generated …',
  `secret_key`    VARCHAR(128)    NULL     COMMENT '签名密钥',
  `retry_times`   INT             NOT NULL DEFAULT 3 COMMENT '重试次数',
  `timeout_ms`    INT             NOT NULL DEFAULT 5000 COMMENT '超时（毫秒）',
  `hook_status`   VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT 'Webhook 状态',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`hook_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Webhook 订阅';

-- O5 Webhook 推送记录
CREATE TABLE `bp_open_webhook_log` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `hook_id`      BIGINT UNSIGNED NOT NULL COMMENT 'Webhook ID',
  `event_type`   VARCHAR(64)     NOT NULL COMMENT '事件类型',
  `event_id`     VARCHAR(64)     NULL     COMMENT '事件ID',
  `payload`      TEXT            NULL     COMMENT '推送内容',
  `push_status`  VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING / SUCCESS / FAILED',
  `retry_count`  INT             NOT NULL DEFAULT 0 COMMENT '重试次数',
  `http_status`  INT             NULL COMMENT 'HTTP 状态码',
  `response_body` VARCHAR(1000)  NULL COMMENT '响应体',
  `push_time`    DATETIME(3)     NULL COMMENT '推送时间',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_hook_time` (`hook_id`,`create_time`),
  KEY `idx_tenant_status` (`tenant_id`,`push_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Webhook 推送记录';


-- =====================================================================
--  系统与日志（sys）
-- =====================================================================

-- S1 数据字典
CREATE TABLE `bp_sys_dict` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NULL     COMMENT '租户ID（NULL 系统内置）',
  `dict_type`    VARCHAR(64)     NOT NULL COMMENT '字典类型',
  `dict_code`    VARCHAR(64)     NOT NULL COMMENT '字典编码',
  `dict_label`   VARCHAR(128)    NOT NULL COMMENT '字典标签',
  `dict_value`   VARCHAR(255)    NULL     COMMENT '字典值',
  `sort_no`      INT             NOT NULL DEFAULT 0 COMMENT '排序号',
  `css_class`    VARCHAR(64)     NULL     COMMENT '样式（标签颜色）',
  `is_default`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否默认',
  `dict_status`  VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '字典状态',
  `remark`       VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_type_code` (`tenant_id`,`dict_type`,`dict_code`),
  KEY `idx_tenant_type` (`tenant_id`,`dict_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据字典';

-- S2 系统参数
CREATE TABLE `bp_sys_config` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NULL     COMMENT '租户ID（NULL 全局）',
  `config_key`    VARCHAR(128)    NOT NULL COMMENT '参数键（如 auth.arrears.stop.threshold）',
  `config_value`  VARCHAR(2000)   NULL     COMMENT '参数值',
  `config_group`  VARCHAR(40)     NULL     COMMENT '分组：SYSTEM / BUSINESS / IOT / NOTIFY / SECURITY',
  `value_type`    VARCHAR(20)     NOT NULL DEFAULT 'STRING' COMMENT '值类型：STRING / INT / DECIMAL / BOOL / JSON',
  `is_encrypted`  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否加密存储',
  `is_system`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否系统级（不可删除）',
  `description`   VARCHAR(500)    NULL     COMMENT '说明',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_key` (`tenant_id`,`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统参数';

-- S3 操作日志
CREATE TABLE `bp_sys_oper_log` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NULL COMMENT '租户ID',
  `trace_id`      VARCHAR(64)     NULL COMMENT '链路追踪ID',
  `user_id`       BIGINT UNSIGNED NULL COMMENT '用户ID',
  `user_name`     VARCHAR(64)     NULL COMMENT '用户名',
  `module`        VARCHAR(64)     NULL     COMMENT '模块',
  `operation`     VARCHAR(128)    NULL     COMMENT '操作描述',
  `biz_type`      VARCHAR(40)     NULL COMMENT '业务类型',
  `biz_id`        BIGINT UNSIGNED NULL COMMENT '业务单据ID',
  `request_method` VARCHAR(10)    NULL COMMENT '请求方法',
  `request_url`   VARCHAR(500)    NULL COMMENT '请求地址',
  `request_params` TEXT           NULL     COMMENT '请求参数（脱敏）',
  `response_result` VARCHAR(2000) NULL     COMMENT '响应结果',
  `success_flag`  TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否成功：1 是 0 否',
  `error_msg`     VARCHAR(1000)   NULL COMMENT '错误信息',
  `client_ip`     VARCHAR(64)     NULL COMMENT '客户端IP',
  `user_agent`    VARCHAR(500)    NULL COMMENT 'UA',
  `duration_ms`   INT             NULL COMMENT '耗时（毫秒）',
  `oper_time`     DATETIME(3)     NOT NULL COMMENT '操作时间',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_time` (`tenant_id`,`oper_time`),
  KEY `idx_tenant_user` (`tenant_id`,`user_id`,`oper_time`),
  KEY `idx_biz` (`tenant_id`,`biz_type`,`biz_id`),
  KEY `idx_trace` (`trace_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志';

-- S4 审计日志（关键动作，不可修改）
CREATE TABLE `bp_sys_audit_log` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `audit_type`    VARCHAR(40)     NOT NULL COMMENT '审计类型：GRANT 授权 / FINANCE 资金 / REVIEW 审核 / PERMISSION 权限变更 / DATA_EXPORT 数据导出 / LOGIN 登录 / SENSITIVE 敏感数据访问',
  `audit_level`   VARCHAR(20)     NOT NULL DEFAULT 'NORMAL' COMMENT '级别：CRITICAL / IMPORTANT / NORMAL',
  `biz_type`      VARCHAR(40)     NULL COMMENT '业务类型',
  `biz_id`        BIGINT UNSIGNED NULL COMMENT '业务单据ID',
  `operator_id`   BIGINT UNSIGNED NULL COMMENT '操作人ID',
  `operator_name` VARCHAR(64)     NULL COMMENT '操作人姓名',
  `target_type`   VARCHAR(40)     NULL     COMMENT '操作对象类型',
  `target_id`     VARCHAR(64)     NULL     COMMENT '操作对象ID',
  `action`        VARCHAR(64)     NULL     COMMENT '动作',
  `before_json`   JSON            NULL     COMMENT '变更前',
  `after_json`    JSON            NULL     COMMENT '变更后',
  `reason`        VARCHAR(500)    NULL     COMMENT '操作依据',
  `client_ip`     VARCHAR(64)     NULL COMMENT '客户端IP',
  `audit_time`    DATETIME(3)     NOT NULL COMMENT '审计时间',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_type_time` (`tenant_id`,`audit_type`,`audit_time`),
  KEY `idx_tenant_operator` (`tenant_id`,`operator_id`,`audit_time`),
  KEY `idx_target` (`tenant_id`,`target_type`,`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志（关键动作，只追加不可修改）';

-- S5 定时任务
CREATE TABLE `bp_sys_job` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NULL     COMMENT '租户ID（NULL 全局任务）',
  `job_code`       VARCHAR(64)     NOT NULL COMMENT '任务编码',
  `job_name`       VARCHAR(128)    NOT NULL COMMENT '任务名称',
  `job_group`      VARCHAR(40)     NULL     COMMENT '分组：BILLING 计费 / RECONCILE 对账 / ALERT 预警 / NOTIFY 通知 / REPORT 报表 / MAINTENANCE 运维',
  `cron_expr`      VARCHAR(64)     NOT NULL COMMENT 'Cron 表达式',
  `handler`        VARCHAR(255)    NOT NULL COMMENT '执行器 Bean 名',
  `param_json`     JSON            NULL     COMMENT '参数',
  `sharding_total` INT             NOT NULL DEFAULT 1 COMMENT '分片总数',
  `timeout_seconds` INT            NULL     COMMENT '超时（秒）',
  `retry_times`    INT             NOT NULL DEFAULT 0 COMMENT '失败重试次数',
  `job_status`     VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED / DISABLED / PAUSED',
  `description`    VARCHAR(500)    NULL COMMENT '说明',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_jobcode` (`tenant_id`,`job_code`,`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务定义';

CREATE TABLE `bp_sys_job_log` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NULL COMMENT '租户ID',
  `job_id`       BIGINT UNSIGNED NOT NULL COMMENT '定时任务ID',
  `job_code`     VARCHAR(64)     NULL COMMENT '任务编码',
  `shard_no`     INT             NOT NULL DEFAULT 0 COMMENT '分片号',
  `run_status`   VARCHAR(20)     NOT NULL COMMENT '状态：RUNNING / SUCCESS / FAILED / TIMEOUT / SKIPPED',
  `start_time`   DATETIME(3)     NOT NULL COMMENT '开始时间',
  `end_time`     DATETIME(3)     NULL COMMENT '结束时间',
  `duration_ms`  INT             NULL COMMENT '耗时（毫秒）',
  `affect_rows`  INT             NULL     COMMENT '影响行数',
  `result_msg`   VARCHAR(2000)   NULL COMMENT '执行结果',
  `error_msg`    VARCHAR(2000)   NULL COMMENT '错误信息',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_job_time` (`job_id`,`start_time`),
  KEY `idx_tenant_status` (`tenant_id`,`run_status`,`start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务执行日志';

-- S6 文件
CREATE TABLE `bp_sys_file` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `file_name`     VARCHAR(255)    NOT NULL COMMENT '原始文件名',
  `file_path`     VARCHAR(500)    NOT NULL COMMENT '存储路径（含 tenant 前缀）',
  `file_url`      VARCHAR(500)    NULL     COMMENT '访问URL',
  `file_type`     VARCHAR(30)     NULL     COMMENT '类型：IMAGE / VIDEO / DOCUMENT / EXCEL / PDF / OTHER',
  `mime_type`     VARCHAR(128)    NULL COMMENT 'MIME 类型',
  `file_size`     BIGINT          NOT NULL DEFAULT 0 COMMENT '大小（字节）',
  `file_md5`      VARCHAR(64)     NULL     COMMENT 'MD5（秒传与去重）',
  `biz_type`      VARCHAR(40)     NULL     COMMENT '业务类型',
  `biz_id`        BIGINT UNSIGNED NULL COMMENT '业务单据ID',
  `storage_type`  VARCHAR(20)     NOT NULL DEFAULT 'MINIO' COMMENT '存储：MINIO / LOCAL / OSS',
  `is_public`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否公开',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_biz` (`tenant_id`,`biz_type`,`biz_id`),
  KEY `idx_md5` (`file_md5`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文件';

-- S7 消息队列消费幂等记录
CREATE TABLE `bp_sys_mq_idempotent` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NULL COMMENT '租户ID',
  `message_id`   VARCHAR(64)     NOT NULL COMMENT '消息ID',
  `consumer`     VARCHAR(128)    NOT NULL COMMENT '消费者标识',
  `idempotent_key` VARCHAR(128)  NULL     COMMENT '业务幂等键',
  `consume_status` VARCHAR(20)   NOT NULL DEFAULT 'SUCCESS' COMMENT '状态：SUCCESS / FAILED',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `expire_time`  DATETIME(3)     NULL     COMMENT '过期时间（用于清理）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_message_consumer` (`message_id`,`consumer`),
  KEY `idx_expire` (`expire_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MQ 消费幂等记录';

-- S8 死信消息（人工处置）
CREATE TABLE `bp_sys_mq_dlq` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NULL COMMENT '租户ID',
  `queue_name`    VARCHAR(128)    NOT NULL COMMENT '原队列名',
  `message_id`    VARCHAR(64)     NULL COMMENT '消息ID',
  `event_type`    VARCHAR(64)     NULL     COMMENT '事件类型',
  `payload`       TEXT            NULL     COMMENT '消息体',
  `fail_reason`   VARCHAR(2000)   NULL COMMENT '失败原因',
  `retry_count`   INT             NOT NULL DEFAULT 0 COMMENT '重试次数',
  `handle_status` VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待处理 / RETRIED 已重投 / DISCARDED 已丢弃 / FIXED 已修复',
  `handle_user_id` BIGINT UNSIGNED NULL COMMENT '处置人ID',
  `handle_time`   DATETIME(3)     NULL COMMENT '处置时间',
  `handle_remark` VARCHAR(500)    NULL COMMENT '处置备注',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`handle_status`,`create_time`),
  KEY `idx_queue` (`queue_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='死信消息（人工处置入口）';

-- ---------------------------------------------------------------------
-- P5 完成：flow(5) + rule(3) + msg(4) + rpt(5) + gov(4) + open(5) + sys(9) = 35 表
-- 累计：111 表
-- ---------------------------------------------------------------------
