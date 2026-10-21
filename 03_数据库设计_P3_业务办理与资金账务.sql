-- =====================================================================
--  云门道业务平台 —— 数据库设计（第三轮）
--  第 3 部分：BC-05 业务办理（资格审核·配租·合同·退出） + BC-06 资金账务
--  目标库：MySQL 8.0+  /  InnoDB  /  utf8mb4
-- =====================================================================

SET NAMES utf8mb4;
USE `bp_platform`;


-- =====================================================================
--  BC-05  业务办理（biz）—— 保障房全业务闭环核心
-- =====================================================================

-- 5.1 申请单（受理）
CREATE TABLE `bp_biz_application` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `application_no`   VARCHAR(64)     NOT NULL COMMENT '申请单号',
  `org_id`           BIGINT UNSIGNED NOT NULL COMMENT '受理组织',
  `person_id`        BIGINT UNSIGNED NOT NULL COMMENT '申请人员',
  `security_type`    VARCHAR(30)     NOT NULL COMMENT '申请保障类型：PUBLIC 公租房 / AFFORDABLE 保租房 / TALENT 人才公寓 / LOW_RENT 廉租',
  `apply_channel`    VARCHAR(30)     NOT NULL COMMENT '申请渠道：ONLINE 线上(小程序/APP) / OFFLINE 线下窗口 / SELF_TERMINAL 自助终端 / BATCH 批量导入',
  `apply_time`       DATETIME(3)     NOT NULL COMMENT '申请时间',
  `family_size`      INT             NOT NULL DEFAULT 1 COMMENT '申请家庭人口数',
  `intent_district`  VARCHAR(64)     NULL     COMMENT '意向区域',
  `intent_project`   BIGINT UNSIGNED NULL     COMMENT '意向项目（组织ID）',
  `intent_layout`    VARCHAR(30)     NULL     COMMENT '意向户型',
  `intent_area_min`  DECIMAL(12,2)   NULL     COMMENT '意向最小面积',
  `intent_area_max`  DECIMAL(12,2)   NULL     COMMENT '意向最大面积',
  `form_data`        JSON            NULL     COMMENT '动态表单数据（按场景/地区配置）',
  `attachment_urls`  VARCHAR(2000)   NULL     COMMENT '附件URL（逗号分隔）',
  `application_status` VARCHAR(30)   NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT 草稿 / SUBMITTED 已提交 / ACCEPTED 已受理 / REVIEWING 审核中 / SUPPLEMENT 补件中 / PASSED 审核通过 / REJECTED 审核不通过 / WITHDRAWN 已撤回 / CANCELLED 已作废',
  `accept_time`      DATETIME(3)     NULL     COMMENT '受理时间',
  `accept_user_id`   BIGINT UNSIGNED NULL     COMMENT '受理人',
  `current_node`     VARCHAR(64)     NULL     COMMENT '当前流程节点',
  `reject_reason`    VARCHAR(1000)   NULL     COMMENT '不通过原因',
  `supplement_demand` VARCHAR(1000)  NULL     COMMENT '补件要求',
  -- ── 政策扩展（C8：广州§25 保障方式双轨 / §22 收入财产 / 成都§34 送达地址 / 重庆§13 分档收入）
  `security_mode`          VARCHAR(20)   NOT NULL DEFAULT 'HOUSE' COMMENT '保障方式：HOUSE 实物配租 / SUBSIDY 租赁补贴（广州双轨）',
  `declared_income`        DECIMAL(14,2) NULL     COMMENT '申报家庭月收入（元）',
  `declared_income_year`   DECIMAL(14,2) NULL     COMMENT '申报家庭年收入（元）',
  `income_per_capita`      DECIMAL(14,2) NULL     COMMENT '人均月收入（元，计算值，用于分档判定）',
  `family_property_amount` DECIMAL(14,2) NULL     COMMENT '申报家庭财产总额（元，广州要求）',
  `income_check_period`    VARCHAR(30)   NULL     COMMENT '收入统计期：LAST_YEAR 上年度 / LAST_12M 前12个月',
  `hukou_type`             VARCHAR(30)   NULL     COMMENT '户籍类型：LOCAL_URBAN 本市城镇 / LOCAL_RURAL 本市农村 / NON_LOCAL 非本地',
  `hukou_address`          VARCHAR(500)  NULL     COMMENT '户籍地址',
  `service_address_id`     BIGINT UNSIGNED NULL   COMMENT '送达地址ID（关联 bp_person_service_address）',
  `compliance_commit_flag` TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否签署真实性承诺书：1 是 0 否',
  `data_share_agree_flag`  TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否书面同意核实申报信息：1 是 0 否',
  `remark`           VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`        VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_appno` (`tenant_id`,`application_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_org_status` (`tenant_id`,`org_id`,`application_status`),
  KEY `idx_tenant_status_time` (`tenant_id`,`application_status`,`apply_time`),
  KEY `idx_tenant_mode_status` (`tenant_id`,`security_mode`,`application_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申请单（受理）';

-- 5.2 审核记录（多级/多部门联审）
CREATE TABLE `bp_biz_review_record` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `application_id`  BIGINT UNSIGNED NOT NULL COMMENT '申请单ID',
  `review_round`    INT             NOT NULL DEFAULT 1 COMMENT '审核轮次',
  `review_stage`    VARCHAR(40)     NOT NULL COMMENT '审核阶段：ACCEPT 受理初审 / FORM 形式审查 / JOINT 多部门联审 / REVIEW 复审 / PUBLICITY 公示 / FINAL 终审',
  `review_dept`     VARCHAR(40)     NULL     COMMENT '审核部门（联审）：REAL_ESTATE 不动产 / CIVIL 民政 / SOCIAL 社保 / FUND 公积金 / POLICE 公安 / MARKET 市场监管 / HOUSING 住建 / OTHER',
  `review_type`     VARCHAR(30)     NOT NULL COMMENT '审核方式：API 接口实时核验 / BATCH 批量比对 / MANUAL 人工核查',
  `review_user_id`  BIGINT UNSIGNED NULL     COMMENT '审核人',
  `review_user_name` VARCHAR(64)    NULL COMMENT '审核人姓名',
  `review_time`     DATETIME(3)     NULL     COMMENT '审核时间',
  `review_result`   VARCHAR(30)     NOT NULL COMMENT '结果：PASS 通过 / REJECT 不通过 / SUPPLEMENT 需补件 / PENDING 待审核',
  `check_items`     JSON            NULL     COMMENT '核验项明细（收入/房产/社保等逐项结果）',
  `score`           DECIMAL(8,2)    NULL     COMMENT '打分（排序用）',
  `review_opinion`  VARCHAR(1000)   NULL     COMMENT '审核意见',
  `adapter_request` JSON            NULL     COMMENT '外部接口请求留痕',
  `adapter_response` JSON           NULL     COMMENT '外部接口响应留痕',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_app` (`tenant_id`,`application_id`,`review_round`),
  KEY `idx_tenant_stage` (`tenant_id`,`review_stage`,`review_result`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审核记录（多级/多部门联审）';

-- 5.3 公示
CREATE TABLE `bp_biz_publicity` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `publicity_no`   VARCHAR(64)     NOT NULL COMMENT '公示编号',
  `publicity_type` VARCHAR(30)     NOT NULL COMMENT '公示类型：QUALIFY 资格公示 / ALLOCATION 配租公示 / EXIT 退出公示',
  `org_id`         BIGINT UNSIGNED NULL     COMMENT '公示组织',
  `title`          VARCHAR(255)    NOT NULL COMMENT '公示标题',
  `content`        TEXT            NULL     COMMENT '公示内容',
  `start_date`     DATE            NOT NULL COMMENT '公示开始日期',
  `end_date`       DATE            NOT NULL COMMENT '公示结束日期',
  `attachment_url` VARCHAR(500)    NULL COMMENT '附件URL',
  `publicity_status` VARCHAR(20)   NOT NULL DEFAULT 'PUBLISHED' COMMENT '状态：DRAFT / PUBLISHED 已发布 / CLOSED 已结束',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_pubno` (`tenant_id`,`publicity_no`),
  KEY `idx_tenant_type_date` (`tenant_id`,`publicity_type`,`start_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公示';

-- 5.4 公示名单明细
CREATE TABLE `bp_biz_publicity_item` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `publicity_id`  BIGINT UNSIGNED NOT NULL COMMENT '公示ID',
  `person_id`     BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `person_name`   VARCHAR(64)     NULL     COMMENT '姓名（公示用，脱敏可配置）',
  `id_card_mask`  VARCHAR(32)     NULL     COMMENT '脱敏身份证',
  `application_id` BIGINT UNSIGNED NULL    COMMENT '申请单ID',
  `objection_status` VARCHAR(20)  NOT NULL DEFAULT 'NONE' COMMENT '异议状态：NONE 无 / RAISED 有异议 / RESOLVED 已处理',
  `objection_content` VARCHAR(1000) NULL  COMMENT '异议内容',
  `objection_result`  VARCHAR(1000) NULL  COMMENT '异议处理结果',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_publicity` (`publicity_id`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公示名单明细（含异议）';

-- 5.5 轮候库
CREATE TABLE `bp_biz_waiting_queue` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `application_id`  BIGINT UNSIGNED NOT NULL COMMENT '申请单ID',
  `security_type`   VARCHAR(30)     NOT NULL COMMENT '保障类型',
  `org_id`          BIGINT UNSIGNED NULL     COMMENT '所属组织/区域',
  `waiting_no`      VARCHAR(64)     NOT NULL COMMENT '轮候号',
  `waiting_rank`    INT             NULL     COMMENT '轮候排名（按打分动态计算）',
  `total_score`     DECIMAL(10,2)   NOT NULL DEFAULT 0 COMMENT '总得分（优先分+轮候时长分+其他）',
  `priority_score`  DECIMAL(8,2)    NOT NULL DEFAULT 0 COMMENT '优先条件分',
  `wait_days`       INT             NOT NULL DEFAULT 0 COMMENT '已轮候天数',
  `enter_time`      DATETIME(3)     NOT NULL COMMENT '进入轮候时间',
  `valid_until`     DATE            NULL     COMMENT '轮候资格有效期',
  `queue_status`    VARCHAR(30)     NOT NULL DEFAULT 'WAITING' COMMENT '状态：WAITING 轮候中 / WON 已中签 / ALLOCATED 已配租 / FROZEN 已冻结 / EXITED 已退出 / EXPIRED 已过期',
  `freeze_reason`   VARCHAR(500)    NULL COMMENT '冻结原因',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_person_type` (`tenant_id`,`person_id`,`security_type`),
  KEY `idx_tenant_status_rank` (`tenant_id`,`queue_status`,`total_score` DESC),
  KEY `idx_tenant_waitingno` (`tenant_id`,`waiting_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='轮候库';

-- 5.6 配租批次
CREATE TABLE `bp_biz_batch` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `batch_no`       VARCHAR(64)     NOT NULL COMMENT '批次号',
  `batch_name`     VARCHAR(128)    NOT NULL COMMENT '批次名称',
  `org_id`         BIGINT UNSIGNED NOT NULL COMMENT '项目组织',
  `security_type`  VARCHAR(30)     NOT NULL COMMENT '保障类型',
  `batch_type`     VARCHAR(30)     NOT NULL COMMENT '批次类型：LOTTERY 摇号 / SELECT 选房 / DIRECT 直接配租 / SUPPLEMENT 递补',
  `house_count`    INT             NOT NULL DEFAULT 0 COMMENT '房源套数',
  `applicant_count` INT            NOT NULL DEFAULT 0 COMMENT '参与人数',
  `signup_start`   DATETIME(3)     NULL     COMMENT '报名开始',
  `signup_end`     DATETIME(3)     NULL     COMMENT '报名结束',
  `lottery_time`   DATETIME(3)     NULL     COMMENT '摇号时间',
  `select_start`   DATETIME(3)     NULL     COMMENT '选房开始',
  `select_end`     DATETIME(3)     NULL     COMMENT '选房结束',
  `lottery_seed`   VARCHAR(128)    NULL     COMMENT '摇号随机种子（公证留痕）',
  `lottery_algo`   VARCHAR(64)     NULL     COMMENT '摇号算法标识',
  `notary_info`    VARCHAR(500)    NULL     COMMENT '公证信息（公证处/公证员/公证书号）',
  `batch_status`   VARCHAR(30)     NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT 草稿 / PUBLISHED 已发布 / SIGNUP 报名中 / LOTTERY 摇号中 / LOTTERY_DONE 摇号完成 / SELECTING 选房中 / ALLOCATED 已配租 / CLOSED 已结束 / CANCELLED 已取消',
  `rule_config`    JSON            NULL     COMMENT '批次规则（限选户型/面积/区域、优先级等）',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_batchno` (`tenant_id`,`batch_no`),
  KEY `idx_tenant_org_status` (`tenant_id`,`org_id`,`batch_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配租批次';

-- 5.7 批次可配房源池
CREATE TABLE `bp_biz_batch_house` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `batch_id`    BIGINT UNSIGNED NOT NULL COMMENT '批次ID',
  `house_id`    BIGINT UNSIGNED NOT NULL COMMENT '房源ID',
  `space_id`    BIGINT UNSIGNED NOT NULL COMMENT '空间ID',
  `in_pool_status` VARCHAR(20)  NOT NULL DEFAULT 'AVAILABLE' COMMENT '池内状态：AVAILABLE 可选 / LOCKED 已锁定 / SELECTED 已选中 / REMOVED 已移出',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_batch_house` (`tenant_id`,`batch_id`,`house_id`),
  KEY `idx_house` (`house_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='批次可配房源池';

-- 5.8 摇号/选房结果
CREATE TABLE `bp_biz_lottery_result` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `batch_id`       BIGINT UNSIGNED NOT NULL COMMENT '批次ID',
  `person_id`      BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `application_id` BIGINT UNSIGNED NULL     COMMENT '申请单ID',
  `waiting_id`     BIGINT UNSIGNED NULL     COMMENT '轮候记录ID',
  `result_type`    VARCHAR(30)     NOT NULL COMMENT '结果类型：WON 中签 / LOST 未中签 / WAITLIST 递补 / GIVE_UP 放弃',
  `lottery_seq`    VARCHAR(64)     NULL     COMMENT '摇号序号（随机生成，公证留痕）',
  `select_seq`     INT             NULL     COMMENT '选房顺序号',
  `house_id`       BIGINT UNSIGNED NULL     COMMENT '选中房源ID',
  `space_id`       BIGINT UNSIGNED NULL     COMMENT '选中空间ID',
  `select_time`    DATETIME(3)     NULL     COMMENT '选房时间',
  `give_up_reason` VARCHAR(500)    NULL     COMMENT '放弃原因',
  `result_status`  VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待确认 / CONFIRMED 已确认配租 / EXPIRED 已过期 / GIVE_UP 已放弃',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_batch` (`tenant_id`,`batch_id`,`result_type`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_house` (`house_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='摇号/选房结果';

-- 5.9 配租单
CREATE TABLE `bp_biz_allocation` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `allocation_no`   VARCHAR(64)     NOT NULL COMMENT '配租单号',
  `batch_id`        BIGINT UNSIGNED NULL     COMMENT '批次ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '承租人',
  `house_id`        BIGINT UNSIGNED NOT NULL COMMENT '房源ID',
  `space_id`        BIGINT UNSIGNED NOT NULL COMMENT '空间ID',
  `allocation_type` VARCHAR(30)     NOT NULL DEFAULT 'LOTTERY' COMMENT '配租方式：LOTTERY 摇号 / SELECT 选房 / DIRECT 直接 / EXCHANGE 换房',
  `allocation_date` DATE            NOT NULL COMMENT '配租日期',
  `plan_rent_start` DATE            NULL     COMMENT '计划起租日',
  `plan_rent_end`   DATE            NULL     COMMENT '计划止租日',
  `allocation_status` VARCHAR(30)   NOT NULL DEFAULT 'PENDING_SIGN' COMMENT '状态：PENDING_SIGN 待签约 / SIGNED 已签约 / CANCELLED 已取消 / EXPIRED 已过期',
  `lock_expire_time` DATETIME(3)    NULL     COMMENT '房源锁定到期时间（超时释放）',
  `give_up_reason`  VARCHAR(500)    NULL     COMMENT '放弃原因',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_allocno` (`tenant_id`,`allocation_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`,`allocation_status`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`,`allocation_status`),
  KEY `idx_lock_expire` (`lock_expire_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配租单';

-- 5.10 合同（独立实体，含全生命周期）
CREATE TABLE `bp_biz_contract` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `contract_no`     VARCHAR(64)     NOT NULL COMMENT '合同编号',
  `contract_type`   VARCHAR(30)     NOT NULL COMMENT '合同类型：PUBLIC_RENTAL 公租房合同 / AFFORDABLE 保租房合同 / TALENT 人才公寓合同 / LEASE 租赁合同 / SERVICE 物业服务合同 / DORMITORY 住宿协议',
  `template_id`     BIGINT UNSIGNED NULL     COMMENT '合同模板ID',
  `allocation_id`   BIGINT UNSIGNED NULL     COMMENT '配租单ID',
  `org_id`          BIGINT UNSIGNED NOT NULL COMMENT '签约组织',
  `account_set_id`  BIGINT UNSIGNED NULL     COMMENT '账套ID（多账套）',
  -- 当事人
  `lessee_person_id` BIGINT UNSIGNED NOT NULL COMMENT '承租人',
  `lessee_name`     VARCHAR(64)     NULL     COMMENT '承租人姓名',
  `lessee_phone`    VARCHAR(64)     NULL     COMMENT '承租人手机号',
  `lessee_id_card_mask` VARCHAR(32) NULL     COMMENT '承租人身份证脱敏',
  `lessor_org_id`   BIGINT UNSIGNED NOT NULL COMMENT '出租方（产权/运营主体）',
  -- 标的
  `house_id`        BIGINT UNSIGNED NOT NULL COMMENT '房源ID',
  `space_id`        BIGINT UNSIGNED NOT NULL COMMENT '空间ID',
  `house_address`   VARCHAR(500)    NULL     COMMENT '房屋地址（快照）',
  `house_area`      DECIMAL(12,2)   NULL     COMMENT '面积（快照）',
  -- 租期
  `lease_start`     DATE            NOT NULL COMMENT '起租日',
  `lease_end`       DATE            NOT NULL COMMENT '止租日',
  `lease_months`    INT             NULL     COMMENT '租期月数',
  -- 金额
  `rent_price`      DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '租金单价',
  `rent_unit`       VARCHAR(20)     NULL     COMMENT '租金单位：AREA_MONTH / HOUSE_MONTH / BED_MONTH / HOUSE_NIGHT',
  `monthly_rent`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '月租金（元）',
  `deposit_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '押金（元）',
  `subsidy_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '月补贴额（元）',
  `actual_pay`      DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '实付月租金（元）',
  `pay_cycle`       VARCHAR(20)     NOT NULL DEFAULT 'MONTH' COMMENT '缴费周期：MONTH 月 / QUARTER 季 / HALF_YEAR 半年 / YEAR 年',
  `pay_day`         INT             NOT NULL DEFAULT 5 COMMENT '每月缴费日',
  `late_fee_rate`   DECIMAL(8,4)    NULL     COMMENT '滞纳金费率（日）',
  -- 签署
  `sign_type`       VARCHAR(20)     NULL     COMMENT '签署方式：ELECTRONIC 电子签章 / PAPER 纸质 / FACE 人脸确认',
  `sign_vendor`     VARCHAR(30)     NULL     COMMENT '电子签章供应商：QYS 契约锁 / ESIGN E签宝 / OTHER',
  `sign_time`       DATETIME(3)     NULL     COMMENT '签署完成时间',
  `sign_file_url`   VARCHAR(500)    NULL     COMMENT '已签合同文件URL',
  `sign_flow_id`    VARCHAR(128)    NULL     COMMENT '第三方签署流程ID',
  -- 状态
  `contract_status` VARCHAR(30)     NOT NULL DEFAULT 'DRAFT' COMMENT '状态：DRAFT 草稿 / PENDING_SIGN 待签约 / SIGNING 签约中 / EFFECTIVE 履约中 / RENEWING 续签中 / EXPIRED 已到期 / TERMINATED 已终止 / CANCELLED 已作废',
  `effective_time`  DATETIME(3)     NULL     COMMENT '生效时间',
  `terminate_time`  DATETIME(3)     NULL     COMMENT '终止时间',
  `terminate_reason` VARCHAR(500)   NULL     COMMENT '终止原因',
  `parent_contract_id` BIGINT UNSIGNED NULL COMMENT '原合同ID（续签/变更来源）',
  -- 联动开关
  `auto_grant`      TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '合同生效自动授权',
  `auto_expire`     TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '合同到期自动失效授权',
  `arrears_stop`    TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '欠费达阈值自动停权',
  `remark`          VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_contractno` (`tenant_id`,`contract_no`),
  KEY `idx_tenant_lessee` (`tenant_id`,`lessee_person_id`,`contract_status`),
  KEY `idx_tenant_house` (`tenant_id`,`house_id`,`contract_status`),
  KEY `idx_tenant_status_end` (`tenant_id`,`contract_status`,`lease_end`),
  KEY `idx_tenant_org` (`tenant_id`,`org_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同（独立实体，全生命周期）';

-- 5.11 合同共同居住人
CREATE TABLE `bp_biz_contract_cohabitant` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `contract_id`   BIGINT UNSIGNED NOT NULL COMMENT '合同ID',
  `person_id`     BIGINT UNSIGNED NULL     COMMENT '人员ID',
  `member_name`   VARCHAR(64)     NOT NULL COMMENT '姓名',
  `id_card_mask`  VARCHAR(32)     NULL     COMMENT '身份证脱敏',
  `relation`      VARCHAR(30)     NULL     COMMENT '关系',
  `is_granted`    TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否已授权开门',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_contract` (`contract_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同共同居住人';

-- 5.12 合同变更/续签记录
CREATE TABLE `bp_biz_contract_change` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `contract_id`    BIGINT UNSIGNED NOT NULL COMMENT '原合同ID',
  `new_contract_id` BIGINT UNSIGNED NULL    COMMENT '新合同ID（续签生成）',
  `change_type`    VARCHAR(30)     NOT NULL COMMENT '变更类型：RENEW 续签 / RENT_ADJUST 租金调整 / PERIOD 租期变更 / LESSEE 承租人变更 / OTHER',
  `change_reason`  VARCHAR(500)    NULL COMMENT '变更原因',
  `before_json`    JSON            NULL     COMMENT '变更前关键字段',
  `after_json`     JSON            NULL     COMMENT '变更后关键字段',
  `approve_status` VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '审批状态：PENDING / APPROVED / REJECTED',
  `effective_date` DATE            NULL     COMMENT '生效日期',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_contract` (`tenant_id`,`contract_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同变更/续签记录';

-- 5.13 退租/腾退单
CREATE TABLE `bp_biz_termination` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `termination_no`   VARCHAR(64)     NOT NULL COMMENT '退租单号',
  `contract_id`      BIGINT UNSIGNED NOT NULL COMMENT '合同ID',
  `house_id`         BIGINT UNSIGNED NOT NULL COMMENT '房源ID',
  `person_id`        BIGINT UNSIGNED NOT NULL COMMENT '承租人',
  `termination_type` VARCHAR(30)     NOT NULL COMMENT '退租类型：NORMAL 正常退租 / EXPEL 违规清退 / EXPIRE 到期不续 / EXCHANGE 换房退出 / OTHER',
  `apply_time`       DATETIME(3)     NULL     COMMENT '申请时间',
  `plan_exit_date`   DATE            NULL     COMMENT '计划退房日期',
  `actual_exit_date` DATE            NULL     COMMENT '实际退房日期',
  `exit_reason`      VARCHAR(500)    NULL     COMMENT '退租原因',
  -- 验房与结算
  `inspect_status`   VARCHAR(20)     NULL     COMMENT '验房状态：PENDING 待验房 / PASSED 通过 / ABNORMAL 有异常',
  `inspect_result`   VARCHAR(1000)   NULL     COMMENT '验房结果',
  `inspect_images`   VARCHAR(2000)   NULL     COMMENT '验房照片（逗号分隔）',
  `damage_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '损坏赔偿金额',
  `settle_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '结算金额（正数退还，负数补缴）',
  `deposit_refund`   DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '押金退还金额',
  `arrears_amount`   DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '欠费金额',
  `settle_status`    VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '结算状态：PENDING / SETTLED / WAIVED',
  `termination_status` VARCHAR(30)   NOT NULL DEFAULT 'APPLYING' COMMENT '状态：APPLYING 申请中 / APPROVING 审批中 / APPROVED 已批准 / REJECTED 已驳回 / COMPLETED 已完成 / CANCELLED 已取消',
  `house_released`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '房源是否已释放回可配池',
  `grant_revoked`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '授权是否已全部回收',
  -- ── 政策扩展（C8：重庆§38 过渡期 / 成都§23 搬迁期 / §24 物品处置与公证 / §41 强制执行）
  `transition_start_date`      DATE          NULL     COMMENT '过渡期起始日（重庆：腾退给3个月过渡期）',
  `transition_end_date`        DATE          NULL     COMMENT '过渡期结束日',
  `transition_months`          INT           NULL     COMMENT '过渡期月数（可配：重庆3 / 成都搬迁期6）',
  `transition_rent_multiplier` DECIMAL(6,3)  NULL     COMMENT '过渡期租金倍率（重庆：期内1.5，期满2.0）',
  `relocation_start_date`      DATE          NULL     COMMENT '搬迁期起始日（成都：不超过6个月）',
  `relocation_end_date`        DATE          NULL     COMMENT '搬迁期结束日',
  `enforce_flag`               TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否进入强制执行：1 是 0 否',
  `enforce_apply_date`         DATE          NULL     COMMENT '申请法院强制执行日期',
  `enforce_court`              VARCHAR(200)  NULL     COMMENT '受理法院',
  `enforce_result`             VARCHAR(1000) NULL     COMMENT '强制执行结果',
  `item_handler_name`          VARCHAR(64)   NULL     COMMENT '物品处置人姓名（成都：承租人可指定）',
  `item_handler_phone`         VARCHAR(32)   NULL     COMMENT '物品处置人电话',
  `notary_flag`                TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否公证机构见证收回：1 是 0 否',
  `notary_no`                  VARCHAR(64)   NULL     COMMENT '公证书编号',
  `ban_reapply_end_date`       DATE          NULL     COMMENT '限制再申请结束日（违规退回：5年内不得再申请）',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`        VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_termno` (`tenant_id`,`termination_no`),
  KEY `idx_tenant_contract` (`tenant_id`,`contract_id`),
  KEY `idx_tenant_status` (`tenant_id`,`termination_status`),
  KEY `idx_tenant_transition` (`tenant_id`,`transition_end_date`),
  KEY `idx_tenant_enforce` (`tenant_id`,`enforce_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退租/腾退单';

-- 5.14 年度复核 / 资格年审
CREATE TABLE `bp_biz_annual_review` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `review_no`       VARCHAR(64)     NOT NULL COMMENT '复核单号',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `contract_id`     BIGINT UNSIGNED NULL     COMMENT '关联合同',
  `house_id`        BIGINT UNSIGNED NULL     COMMENT '关联房源',
  `review_year`     VARCHAR(10)     NOT NULL COMMENT '复核年度（如 2026）',
  `review_batch`    VARCHAR(64)     NULL     COMMENT '复核批次',
  `review_type`     VARCHAR(30)     NOT NULL DEFAULT 'ANNUAL' COMMENT '类型：ANNUAL 年度复核 / DYNAMIC 动态核查 / SPECIAL 专项核查',
  `trigger_reason`  VARCHAR(500)    NULL     COMMENT '触发原因（如系统预警转来）',
  `check_result`    JSON            NULL     COMMENT '核验结果明细（收入/房产/人口变化等）',
  `review_result`   VARCHAR(30)     NULL     COMMENT '复核结果：KEEP 保留资格 / ADJUST 调整（租金/房源） / EXIT 退出 / PENDING 待定',
  `adjust_content`  VARCHAR(1000)   NULL     COMMENT '调整内容',
  `review_status`   VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待复核 / REVIEWING 复核中 / DONE 已完成 / OVERDUE 已逾期',
  `review_date`     DATE            NULL     COMMENT '复核日期',
  `next_review_date` DATE           NULL     COMMENT '下次复核日期',
  `review_user_id`  BIGINT UNSIGNED NULL     COMMENT '复核人',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_reviewno` (`tenant_id`,`review_no`),
  KEY `idx_tenant_person_year` (`tenant_id`,`person_id`,`review_year`),
  KEY `idx_tenant_status` (`tenant_id`,`review_status`,`next_review_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='年度复核/资格年审';

-- 5.15 换房记录
CREATE TABLE `bp_biz_exchange` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `exchange_no`      VARCHAR(64)     NOT NULL COMMENT '换房单号',
  `person_id`        BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `old_contract_id`  BIGINT UNSIGNED NULL     COMMENT '原合同ID',
  `old_house_id`     BIGINT UNSIGNED NOT NULL COMMENT '原房源ID',
  `new_house_id`     BIGINT UNSIGNED NOT NULL COMMENT '新房源ID',
  `new_contract_id`  BIGINT UNSIGNED NULL     COMMENT '新合同ID',
  `exchange_type`    VARCHAR(30)     NOT NULL COMMENT '换房类型：VOLUNTARY 自愿 / ADJUST 调整 / EXPEL_RELOCATE 清退安置',
  `exchange_reason`  VARCHAR(500)    NULL COMMENT '换房原因',
  `exchange_status`  VARCHAR(30)     NOT NULL DEFAULT 'APPLYING' COMMENT '状态：APPLYING / APPROVING / APPROVED / COMPLETED / REJECTED',
  `grant_migrated`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '权限是否已自动迁移',
  -- ── 政策扩展（C8：成都§15 限1次互换 / 重庆§33 应换不换按1.5倍计租）
  `exchange_times`       INT           NOT NULL DEFAULT 1 COMMENT '本租期内第几次换房（成都：限1次）',
  `is_forced`            TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否应换房（期满因合住人数减少不符户型标准的应当换房）',
  `no_exchange_flag`     TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '应换不换标记：1 是 0 否（重庆：按1.5倍计租）',
  `rent_multiplier`      DECIMAL(6,3)  NULL     COMMENT '换房后租金倍率（应换不换为1.5）',
  `family_size_before`   INT           NULL     COMMENT '换房前家庭人数',
  `family_size_after`    INT           NULL     COMMENT '换房后家庭人数',
  `exchange_reason_code` VARCHAR(50)   NULL     COMMENT '换房原因码：MARRIAGE 婚姻 / BIRTH 生育 / COHABIT 合住增加 / EMPLOYMENT 就业 / SCHOOL 子女就学 / TRANSPORT 出行不便 / OTHER 其他',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_exchno` (`tenant_id`,`exchange_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_forced` (`tenant_id`,`is_forced`,`no_exchange_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='换房记录（权限自动迁移）';

-- 5.16 合同模板
CREATE TABLE `bp_biz_contract_template` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `template_code` VARCHAR(64)     NOT NULL COMMENT '模板编码',
  `template_name` VARCHAR(128)    NOT NULL COMMENT '模板名称',
  `contract_type` VARCHAR(30)     NOT NULL COMMENT '合同类型',
  `security_type` VARCHAR(30)     NULL     COMMENT '适用保障类型',
  `file_url`      VARCHAR(500)    NOT NULL COMMENT '模板文件URL（docx）',
  `variables`     JSON            NULL     COMMENT '变量定义（占位符清单）',
  `version`       INT             NOT NULL DEFAULT 1 COMMENT '版本',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_tplcode_ver` (`tenant_id`,`template_code`,`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同模板';


-- =====================================================================
--  BC-06  资金账务（fin）
-- =====================================================================

-- 6.1 收费项目
CREATE TABLE `bp_fin_fee_item` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `item_code`    VARCHAR(64)     NOT NULL COMMENT '收费项目编码',
  `item_name`    VARCHAR(128)    NOT NULL COMMENT '收费项目名称（租金/物业费/车位费/水电费/垃圾清运费/能耗费…）',
  `item_type`    VARCHAR(30)     NOT NULL COMMENT '类型：RENT 租金 / PROPERTY 物业费 / PARKING 停车费 / ENERGY 能耗费 / DEPOSIT 押金 / LATE_FEE 滞纳金 / OTHER',
  `security_type` VARCHAR(30)    NULL     COMMENT '适用保障类型（NULL 通用）',
  `calc_mode`    VARCHAR(30)     NOT NULL COMMENT '计费方式：FIXED 固定额 / BY_AREA 按面积 / BY_HOUSE 按套 / BY_PERSON 按人 / BY_BED 按床位 / BY_NIGHT 按夜 / METER 按抄表',
  `unit_price`   DECIMAL(14,4)   NULL     COMMENT '默认单价',
  `unit`         VARCHAR(20)     NULL     COMMENT '单位（元/㎡·月 等）',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `is_deleted`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`    VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_itemcode` (`tenant_id`,`item_code`,`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收费项目';

-- 6.2 计费规则（政策租金/阶梯/减免）
CREATE TABLE `bp_fin_billing_rule` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `rule_code`     VARCHAR(64)     NOT NULL COMMENT '规则编码',
  `rule_name`     VARCHAR(128)    NOT NULL COMMENT '规则名称',
  `fee_item_id`   BIGINT UNSIGNED NOT NULL COMMENT '收费项目ID',
  `org_id`        BIGINT UNSIGNED NULL     COMMENT '适用组织（NULL 全租户）',
  `house_type`    VARCHAR(30)     NULL     COMMENT '适用房源类型',
  `security_type` VARCHAR(30)     NULL     COMMENT '适用保障类型',
  `income_level`  VARCHAR(30)     NULL     COMMENT '适用收入档位',
  `rule_type`     VARCHAR(30)     NOT NULL COMMENT '规则类型：STANDARD 标准价 / TIERED 阶梯 / DISCOUNT 折扣 / EXEMPT 减免',
  `price_config`  JSON            NOT NULL COMMENT '价格配置（标准价/阶梯区间/折扣率/减免额）',
  `effective_start` DATE          NOT NULL COMMENT '生效开始',
  `effective_end` DATE            NULL     COMMENT '生效结束',
  `priority`      INT             NOT NULL DEFAULT 0 COMMENT '优先级（多规则命中时取高）',
  `rule_version`  INT             NOT NULL DEFAULT 1 COMMENT '版本',
  `approve_status` VARCHAR(20)    NOT NULL DEFAULT 'APPROVED' COMMENT '审批状态（租金定价管控）：PENDING / APPROVED / REJECTED',
  `approve_by_id` BIGINT UNSIGNED NULL     COMMENT '审批人（政府限价审批）',
  `approve_time`  DATETIME(3)     NULL COMMENT '审批时间',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_rulecode_ver` (`tenant_id`,`rule_code`,`rule_version`),
  KEY `idx_tenant_item` (`tenant_id`,`fee_item_id`),
  KEY `idx_tenant_effective` (`tenant_id`,`effective_start`,`effective_end`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='计费规则（政策租金/阶梯/减免，含政府限价审批）';

-- 6.3 账单
CREATE TABLE `bp_fin_bill` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `bill_no`        VARCHAR(64)     NOT NULL COMMENT '账单号',
  `account_set_id` BIGINT UNSIGNED NULL     COMMENT '账套ID',
  `org_id`         BIGINT UNSIGNED NOT NULL COMMENT '组织',
  `contract_id`    BIGINT UNSIGNED NULL     COMMENT '合同ID',
  `house_id`       BIGINT UNSIGNED NULL     COMMENT '房源ID',
  `space_id`       BIGINT UNSIGNED NULL     COMMENT '空间ID',
  `person_id`      BIGINT UNSIGNED NULL     COMMENT '缴费人',
  `payer_name`     VARCHAR(64)     NULL     COMMENT '缴费人姓名',
  `payer_phone`    VARCHAR(64)     NULL     COMMENT '缴费人手机号',
  `fee_item_id`    BIGINT UNSIGNED NOT NULL COMMENT '收费项目ID',
  `bill_period`    VARCHAR(20)     NULL     COMMENT '账期（如 2026-10）',
  `period_start`   DATE            NOT NULL COMMENT '费用起始日',
  `period_end`     DATE            NOT NULL COMMENT '费用截止日',
  `bill_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '应收金额',
  `discount_amount` DECIMAL(14,2)  NOT NULL DEFAULT 0 COMMENT '减免金额',
  `late_fee`       DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '滞纳金',
  `paid_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '已收金额',
  `waived_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '已免金额',
  `payable_amount` DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '应付金额（应收-减免+滞纳金-已收-已免）',
  `due_date`       DATE            NOT NULL COMMENT '缴费截止日',
  `bill_status`    VARCHAR(30)     NOT NULL DEFAULT 'UNPAID' COMMENT '状态：UNPAID 未缴 / PARTIAL 部分缴 / PAID 已缴 / OVERDUE 已逾期 / WAIVED 已免除 / CANCELLED 已作废',
  `overdue_days`   INT             NOT NULL DEFAULT 0 COMMENT '逾期天数',
  `generate_type`  VARCHAR(20)     NOT NULL DEFAULT 'AUTO' COMMENT '生成方式：AUTO 自动 / MANUAL 手工 / IMPORT 导入',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_billno` (`tenant_id`,`bill_no`),
  KEY `idx_tenant_person_status` (`tenant_id`,`person_id`,`bill_status`),
  KEY `idx_tenant_contract` (`tenant_id`,`contract_id`),
  KEY `idx_tenant_due_status` (`tenant_id`,`due_date`,`bill_status`),
  KEY `idx_tenant_period` (`tenant_id`,`bill_period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账单';

-- 6.4 收款单
CREATE TABLE `bp_fin_payment` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `payment_no`      VARCHAR(64)     NOT NULL COMMENT '收款单号',
  `account_set_id`  BIGINT UNSIGNED NULL     COMMENT '账套ID',
  `org_id`          BIGINT UNSIGNED NOT NULL COMMENT '组织',
  `person_id`       BIGINT UNSIGNED NULL     COMMENT '缴费人',
  `payer_name`      VARCHAR(64)     NULL COMMENT '缴费人姓名',
  `pay_amount`      DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '收款金额',
  `pay_channel`     VARCHAR(30)     NOT NULL COMMENT '渠道：WECHAT 微信 / ALIPAY 支付宝 / BANK 银行代扣 / BANK_TRANSFER 银行转账 / CASH 现金 / POS 刷卡 / SELF_TERMINAL 自助机 / OTHER',
  `pay_time`        DATETIME(3)     NOT NULL COMMENT '付款时间',
  `trade_no`        VARCHAR(128)    NULL     COMMENT '第三方交易号',
  `pay_status`      VARCHAR(20)     NOT NULL DEFAULT 'SUCCESS' COMMENT '状态：PENDING 待支付 / SUCCESS 成功 / FAILED 失败 / REFUNDED 已退款',
  `reconcile_status` VARCHAR(20)    NOT NULL DEFAULT 'UNRECONCILED' COMMENT '核销状态：UNRECONCILED 未核销 / RECONCILED 已核销 / PARTIAL 部分核销',
  `reconciled_amount` DECIMAL(14,2) NOT NULL DEFAULT 0 COMMENT '已核销金额',
  `unknown_flag`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否未知款项（来源去向不明，待查证后关联应收）',
  `operator_id`     BIGINT UNSIGNED NULL     COMMENT '收款操作人',
  `remark`          VARCHAR(500)    NULL COMMENT '备注',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_paymentno` (`tenant_id`,`payment_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_time` (`tenant_id`,`pay_time`),
  KEY `idx_tenant_trade` (`trade_no`),
  KEY `idx_tenant_unknown` (`tenant_id`,`unknown_flag`,`reconcile_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收款单（含未知款项挂账）';

-- 6.5 收款核销明细
CREATE TABLE `bp_fin_payment_allocate` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `payment_id`  BIGINT UNSIGNED NOT NULL COMMENT '收款单ID',
  `bill_id`     BIGINT UNSIGNED NOT NULL COMMENT '账单ID',
  `allocate_amount` DECIMAL(14,2) NOT NULL COMMENT '核销金额',
  `allocate_type` VARCHAR(20)    NOT NULL DEFAULT 'PAY' COMMENT '核销类型：PAY 缴费核销 / REFUND 退款冲销',
  `create_by`   VARCHAR(64)     NULL COMMENT '创建人',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_payment` (`payment_id`),
  KEY `idx_bill` (`bill_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收款核销明细';

-- 6.6 押金台账
CREATE TABLE `bp_fin_deposit` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `contract_id`    BIGINT UNSIGNED NOT NULL COMMENT '合同ID',
  `person_id`      BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `deposit_amount` DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '应收押金',
  `paid_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '已收押金',
  `deduct_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '已抵扣金额',
  `refund_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '已退还金额',
  `balance_amount` DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '押金余额',
  `deposit_status` VARCHAR(20)     NOT NULL DEFAULT 'HELD' COMMENT '状态：HELD 已收取 / PARTIAL_REFUND 部分退还 / REFUNDED 已退还 / DEDUCTED 已抵扣',
  -- ── 政策扩展（C8：成都§18 保证金不超过1000元；廉租标准免收）
  `cap_amount`     DECIMAL(14,2)   NULL     COMMENT '政策规定上限（成都：1000元）',
  `is_exempt`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否免收（廉租标准免收）：1 是 0 否',
  `exempt_reason`  VARCHAR(200)    NULL     COMMENT '免收原因',
  `over_cap_flag`  TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否超政策上限：1 超限 0 合规',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_contract` (`tenant_id`,`contract_id`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='押金台账';

-- 6.7 补贴标准
CREATE TABLE `bp_fin_subsidy_standard` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `standard_code`  VARCHAR(64)     NOT NULL COMMENT '标准编码',
  `standard_name`  VARCHAR(128)    NOT NULL COMMENT '标准名称',
  `security_type`  VARCHAR(30)     NOT NULL COMMENT '保障类型：PUBLIC / AFFORDABLE / TALENT / LOW_RENT',
  `org_id`         BIGINT UNSIGNED NULL     COMMENT '适用组织',
  `income_level`   VARCHAR(30)     NULL     COMMENT '适用收入档位',
  `family_type`    VARCHAR(30)     NULL     COMMENT '适用家庭类型',
  `talent_level`   VARCHAR(30)     NULL     COMMENT '适用人才层次',
  `subsidy_mode`   VARCHAR(30)     NOT NULL COMMENT '补贴方式：FIXED 定额 / BY_AREA 按面积 / BY_PERSON 按人 / RATIO 按租金比例 / CAP 封顶',
  `subsidy_value`  DECIMAL(14,4)   NOT NULL COMMENT '补贴值（金额/单价/比例）',
  `max_amount`     DECIMAL(14,2)   NULL     COMMENT '单户月度封顶金额',
  `effective_start` DATE           NOT NULL COMMENT '生效开始时间',
  `effective_end`  DATE            NULL COMMENT '生效结束时间',
  `status`         VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_stdcode` (`tenant_id`,`standard_code`,`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='补贴标准';

-- 6.8 补贴发放记录
CREATE TABLE `bp_fin_subsidy_record` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `record_no`       VARCHAR(64)     NOT NULL COMMENT '发放记录号',
  `standard_id`     BIGINT UNSIGNED NULL     COMMENT '补贴标准ID',
  `contract_id`     BIGINT UNSIGNED NOT NULL COMMENT '合同ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '受益人',
  `person_name`     VARCHAR(64)     NULL COMMENT '姓名',
  `org_id`          BIGINT UNSIGNED NULL COMMENT '组织ID',
  `subsidy_period`  VARCHAR(20)     NOT NULL COMMENT '补贴期间（如 2026-10）',
  `subsidy_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '应发金额',
  `paid_amount`     DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '实发金额',
  `pay_mode`        VARCHAR(30)     NOT NULL COMMENT '发放方式：FINANCE 财政直发 / BANK 银行代发 / OFFSET_RENT 抵扣租金',
  `bank_account`    VARCHAR(128)    NULL     COMMENT '收款账号（加密）',
  `record_status`   VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待发放 / PAYING 发放中 / SUCCESS 已发放 / FAILED 发放失败 / RETURNED 已退回',
  `finance_batch_no` VARCHAR(64)    NULL     COMMENT '财政/银行批次号',
  `fail_reason`     VARCHAR(500)    NULL COMMENT '失败原因',
  `issue_date`      DATE            NULL     COMMENT '发放日期',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_recordno` (`tenant_id`,`record_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`,`subsidy_period`),
  KEY `idx_tenant_status` (`tenant_id`,`record_status`),
  KEY `idx_tenant_batch` (`finance_batch_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='补贴发放记录';

-- 6.9 催缴记录
CREATE TABLE `bp_fin_dunning_record` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `bill_id`       BIGINT UNSIGNED NOT NULL COMMENT '账单ID',
  `person_id`     BIGINT UNSIGNED NULL     COMMENT '欠费人',
  `dunning_no`    INT             NOT NULL DEFAULT 1 COMMENT '催缴次数',
  `dunning_type`  VARCHAR(30)     NOT NULL COMMENT '催缴方式：SMS 短信 / WECHAT 微信 / PHONE 电话 / VISIT 上门 / NOTICE 通知书 / PLATFORM 平台消息',
  `dunning_time`  DATETIME(3)     NOT NULL COMMENT '催缴时间',
  `dunning_content` VARCHAR(1000) NULL     COMMENT '催缴内容',
  `dunning_result` VARCHAR(500)   NULL     COMMENT '催缴结果',
  `evidence_url`  VARCHAR(1000)   NULL     COMMENT '佐证（上门照片/通话记录）',
  `operator_id`   BIGINT UNSIGNED NULL COMMENT '操作人ID',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_bill` (`tenant_id`,`bill_id`),
  KEY `idx_tenant_person_time` (`tenant_id`,`person_id`,`dunning_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='催缴记录';

-- 6.10 欠费停权处置记录
CREATE TABLE `bp_fin_arrears_action` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `action_no`       VARCHAR(64)     NOT NULL COMMENT '处置单号',
  `contract_id`     BIGINT UNSIGNED NOT NULL COMMENT '合同ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `arrears_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '欠费金额',
  `overdue_days`    INT             NOT NULL DEFAULT 0 COMMENT '逾期天数',
  `trigger_type`    VARCHAR(30)     NOT NULL COMMENT '触发方式：AUTO 自动 / MANUAL 手动',
  `action_type`     VARCHAR(30)     NOT NULL COMMENT '处置动作：NOTIFY 通知 / FREEZE 冻结权限 / UNFREEZE 解冻 / RESTRICT 限制续租 / EXPIRE 到期不续 / LEGAL 司法',
  `freeze_scope`    VARCHAR(30)     NULL     COMMENT '冻结范围：ALL 全部设备 / ROOM_LOCK 房门锁 / EXCLUDE_MAIN_DOOR 排除大门门禁（安全底线）',
  `action_status`   VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING / EXECUTED 已执行 / REVOKED 已撤销 / FAILED',
  `execute_time`    DATETIME(3)     NULL     COMMENT '执行时间',
  `grant_task_id`   BIGINT UNSIGNED NULL     COMMENT '关联授权任务ID',
  `revoke_reason`   VARCHAR(500)    NULL     COMMENT '撤销原因（如已缴费）',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_actionno` (`tenant_id`,`action_no`),
  KEY `idx_tenant_contract` (`tenant_id`,`contract_id`),
  KEY `idx_tenant_status` (`tenant_id`,`action_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='欠费停权处置记录（含冻结范围与安全底线）';

-- 6.11 财务对账记录
CREATE TABLE `bp_fin_reconcile` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `reconcile_no`   VARCHAR(64)     NOT NULL COMMENT '对账单号',
  `account_set_id` BIGINT UNSIGNED NULL COMMENT '账套ID',
  `reconcile_date` DATE            NOT NULL COMMENT '对账日期',
  `reconcile_type` VARCHAR(30)     NOT NULL COMMENT '类型：CHANNEL 渠道对账 / DAILY 日终对账 / MANUAL 手工对账',
  `pay_channel`    VARCHAR(30)     NULL     COMMENT '对账渠道',
  `system_amount`  DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '系统金额',
  `channel_amount` DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '渠道金额',
  `diff_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '差异金额',
  `diff_count`     INT             NOT NULL DEFAULT 0 COMMENT '差异笔数',
  `reconcile_status` VARCHAR(20)   NOT NULL DEFAULT 'MATCHED' COMMENT '状态：MATCHED 一致 / DIFF 有差异 / HANDLED 已处理',
  `diff_detail_url` VARCHAR(500)   NULL     COMMENT '差异明细文件URL',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_reconno` (`tenant_id`,`reconcile_no`),
  KEY `idx_tenant_date` (`tenant_id`,`reconcile_date`,`reconcile_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务对账记录';

-- 6.12 退款单
CREATE TABLE `bp_fin_refund` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `refund_no`     VARCHAR(64)     NOT NULL COMMENT '退款单号',
  `payment_id`    BIGINT UNSIGNED NULL     COMMENT '原收款单ID',
  `person_id`     BIGINT UNSIGNED NULL     COMMENT '退款人',
  `contract_id`   BIGINT UNSIGNED NULL     COMMENT '合同ID',
  `refund_amount` DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT '退款金额',
  `refund_reason` VARCHAR(500)    NULL     COMMENT '退款原因',
  `refund_type`   VARCHAR(30)     NOT NULL COMMENT '类型：DEPOSIT 押金退还 / OVERPAY 多缴退还 / OTHER',
  `refund_channel` VARCHAR(30)    NULL     COMMENT '退款渠道：ORIGINAL 原路退回 / BANK 银行转账 / CASH 现金',
  `refund_status` VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待审批 / APPROVED 已批准 / SUCCESS 已退款 / FAILED 失败 / REJECTED 已驳回',
  `approve_by_id` BIGINT UNSIGNED NULL COMMENT '审批人ID',
  `approve_time`  DATETIME(3)     NULL COMMENT '审批时间',
  `refund_time`   DATETIME(3)     NULL COMMENT '退款时间',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_refundno` (`tenant_id`,`refund_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_status` (`tenant_id`,`refund_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退款单（含审批）';

-- 6.13 资金流水（账务数据校验与审计）
CREATE TABLE `bp_fin_cash_flow` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `account_set_id`  BIGINT UNSIGNED NULL     COMMENT '账套ID',
  `flow_no`         VARCHAR(64)     NOT NULL COMMENT '流水号',
  `flow_type`       VARCHAR(30)     NOT NULL COMMENT '类型：INCOME 收入 / EXPENSE 支出 / TRANSFER 转账 / ADJUST 调整',
  `biz_type`        VARCHAR(30)     NULL     COMMENT '业务类型：BILL 账单 / PAYMENT 收款 / REFUND 退款 / SUBSIDY 补贴 / OTHER',
  `biz_id`          BIGINT UNSIGNED NULL     COMMENT '业务单据ID',
  `amount`          DECIMAL(14,2)   NOT NULL COMMENT '金额（正负）',
  `balance_after`   DECIMAL(16,2)   NULL     COMMENT '变动后余额',
  `flow_time`       DATETIME(3)     NOT NULL COMMENT '发生时间',
  `verify_status`   VARCHAR(20)     NOT NULL DEFAULT 'UNVERIFIED' COMMENT '校验状态：UNVERIFIED 未校验 / VERIFIED 已校验 / ABNORMAL 异常',
  `verify_remark`   VARCHAR(500)    NULL     COMMENT '校验备注（业务数据变更后的账务一致性校验）',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_flowno` (`tenant_id`,`flow_no`),
  KEY `idx_tenant_time` (`tenant_id`,`flow_time`),
  KEY `idx_tenant_biz` (`tenant_id`,`biz_type`,`biz_id`),
  KEY `idx_verify` (`tenant_id`,`verify_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资金流水（含账务数据校验）';


-- 5.17 申诉与异议处理（政策扩展 C8：重庆§19 申诉10工作日 / 广州§25(五) 异议复核）
CREATE TABLE `bp_biz_appeal` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `appeal_no`       VARCHAR(64)     NOT NULL COMMENT '申诉/异议单号',
  `biz_type`        VARCHAR(30)     NOT NULL COMMENT '业务类型：APPLICATION 申请 / REVIEW 审核 / ANNUAL_REVIEW 年度核查 / PUBLICITY 公示异议 / EXIT 退出',
  `biz_id`          BIGINT UNSIGNED NOT NULL COMMENT '关联业务ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '申请人/人员ID',
  `org_id`          BIGINT UNSIGNED NULL     COMMENT '受理组织ID',
  `appeal_type`     VARCHAR(30)     NOT NULL COMMENT '类型：SUBMIT 申诉 / OBJECTION 公示异议',
  `appeal_reason`   VARCHAR(2000)   NOT NULL COMMENT '申诉/异议理由',
  `appeal_evidence` VARCHAR(2000)   NULL     COMMENT '证据材料URL（逗号分隔）',
  `deadline_time`   DATETIME(3)     NULL     COMMENT '申诉截止时间（依据政策时限计算，如收到告知起10个工作日）',
  `appeal_time`     DATETIME(3)     NOT NULL COMMENT '提出时间',
  `accept_time`     DATETIME(3)     NULL     COMMENT '受理时间',
  `accept_user_id`  BIGINT UNSIGNED NULL     COMMENT '受理人ID',
  `handle_user_id`  BIGINT UNSIGNED NULL     COMMENT '处理人ID',
  `handle_time`     DATETIME(3)     NULL     COMMENT '处理时间',
  `handle_result`   VARCHAR(2000)   NULL     COMMENT '调查核实情况',
  `review_opinion`  VARCHAR(2000)   NULL     COMMENT '复核意见',
  `appeal_status`   VARCHAR(30)     NOT NULL DEFAULT 'SUBMITTED' COMMENT '状态：SUBMITTED 已提交 / ACCEPTED 已受理 / INVESTIGATING 调查中 / UPHELD 异议成立 / REJECTED 异议不成立 / WITHDRAWN 已撤回 / TIMEOUT 超期',
  `result_effect`   VARCHAR(30)     NULL     COMMENT '结果影响：RESTORE 恢复资格 / CANCEL 取消资格 / ADJUST 调整标准 / NONE 无影响',
  `notify_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '告知状态：PENDING 待告知 / SENT 已告知',
  `create_by`       VARCHAR(64)     NULL     COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL     COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_appeal_no` (`tenant_id`,`appeal_no`),
  KEY `idx_tenant_biz` (`tenant_id`,`biz_type`,`biz_id`),
  KEY `idx_tenant_person_time` (`tenant_id`,`person_id`,`appeal_time`),
  KEY `idx_tenant_status` (`tenant_id`,`appeal_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='申诉与异议处理';

-- 5.18 信用惩戒记录（政策扩展 C8：成都§31 五年内不得再申请+信用平台 / 重庆§40）
CREATE TABLE `bp_biz_credit_record` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `record_no`       VARCHAR(64)     NOT NULL COMMENT '惩戒记录编号',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `biz_type`        VARCHAR(30)     NULL     COMMENT '关联业务类型：EXIT 退出 / CONTRACT 合同 / APPLICATION 申请',
  `biz_id`          BIGINT UNSIGNED NULL     COMMENT '关联业务ID',
  `violation_type`  VARCHAR(50)     NOT NULL COMMENT '违规类型：FALSE_INFO 提供虚假信息 / SUBLEASE 转租出借 / STRUCTURE 破坏结构 / CHANGE_USE 改变用途 / VACANT 长期空置 / ILLEGAL 从事违法活动 / ARREARS 恶意欠租 / OTHER 其他',
  `violation_desc`  VARCHAR(2000)   NULL     COMMENT '违规情况描述',
  `evidence_url`    VARCHAR(2000)   NULL     COMMENT '证据材料URL（逗号分隔）',
  `sanction_type`   VARCHAR(50)     NOT NULL COMMENT '惩戒措施：TERMINATE 终止资格 / BAN_APPLY 限制申请 / CREDIT_PLATFORM 推送信用平台 / FINE 罚款 / OTHER 其他',
  `ban_years`       INT             NULL     COMMENT '限制申请年限（政策：5年）',
  `ban_start_date`  DATE            NULL     COMMENT '限制起始日期',
  `ban_end_date`    DATE            NULL     COMMENT '限制结束日期',
  `push_platform`   VARCHAR(64)     NULL     COMMENT '推送平台名称（如 四川住房保障管理服务平台）',
  `push_status`     VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '推送状态：PENDING 待推送 / PUSHED 已推送 / FAILED 推送失败 / NONE 不推送',
  `push_time`       DATETIME(3)     NULL     COMMENT '推送时间',
  `decide_org_id`   BIGINT UNSIGNED NULL     COMMENT '决定机关组织ID',
  `decide_user_id`  BIGINT UNSIGNED NULL     COMMENT '决定人ID',
  `decide_time`     DATETIME(3)     NULL     COMMENT '决定时间',
  `legal_doc_no`    VARCHAR(64)     NULL     COMMENT '法律文书编号',
  `status`          VARCHAR(20)     NOT NULL DEFAULT 'EFFECTIVE' COMMENT '状态：EFFECTIVE 生效中 / EXPIRED 已解除 / REVOKED 已撤销',
  `remark`          VARCHAR(500)    NULL     COMMENT '备注',
  `create_by`       VARCHAR(64)     NULL     COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL     COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_record_no` (`tenant_id`,`record_no`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`,`status`),
  KEY `idx_tenant_ban` (`tenant_id`,`ban_end_date`,`status`),
  KEY `idx_tenant_violation` (`tenant_id`,`violation_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='信用惩戒记录';

-- 5.19 优先配租对象（政策扩展 C8：重庆§22 四类 / 成都§10 八类 / 广州多类）
CREATE TABLE `bp_biz_priority_object` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `priority_type`   VARCHAR(50)     NOT NULL COMMENT '优先类型（可配字典）：DIBao 低保 / TeKun 分散供养特困 / DiBaoBianYuan 低保边缘 / YouFu 优抚对象 / CanJi 残疾人 / CanJiJunRen 残疾军人 / LieShi 烈士遗属 / GuEr 孤儿 / JiSheng 计生特扶 / LaoNian 均满60岁 / ErHai 二孩以上 / FangChanZhengShou 征收过渡 / Other 其他',
  `priority_level`  INT             NOT NULL DEFAULT 1 COMMENT '优先级（数值越小越优先）',
  `certify_org`     VARCHAR(128)    NULL     COMMENT '认定部门',
  `certify_doc_no`  VARCHAR(64)     NULL     COMMENT '认定文号/证件号',
  `certify_date`    DATE            NULL     COMMENT '认定日期',
  `valid_from`      DATE            NULL     COMMENT '有效期起',
  `valid_to`        DATE            NULL     COMMENT '有效期止（空=长期）',
  `status`          VARCHAR(20)     NOT NULL DEFAULT 'VALID' COMMENT '状态：VALID 有效 / EXPIRED 已过期 / REVOKED 已撤销',
  `evidence_url`    VARCHAR(1000)   NULL     COMMENT '证明材料URL（逗号分隔）',
  `remark`          VARCHAR(500)    NULL     COMMENT '备注',
  `create_by`       VARCHAR(64)     NULL     COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL     COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_person_type` (`tenant_id`,`person_id`,`priority_type`),
  KEY `idx_tenant_type_valid` (`tenant_id`,`priority_type`,`status`,`valid_to`),
  KEY `idx_tenant_person_status` (`tenant_id`,`person_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='优先配租对象明细';


-- ---------------------------------------------------------------------
-- P3 完成：BC-05 业务办理（19 表）、BC-06 资金账务（13 表）= 32 表
-- 累计：76 表
-- ---------------------------------------------------------------------
