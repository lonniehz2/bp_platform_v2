-- =============================================================================
--  P7 · 短租订单（酒店 / 民宿 / 网约房）
--  为什么需要独立表：
--    长租合同以"日期级租期 + 月租金"表达；短租需要"时刻级入住/退房 + 房晚计价"，
--    且网约房有实名登记要求。用独立订单表旁挂，不污染长租合同模型。
--  与日房态联动：下单即占 bp_asset_house_calendar 的 [入住日, 退房日) 区间。
-- =============================================================================

CREATE TABLE `bp_biz_short_rent_order` (
  `id`              BIGINT UNSIGNED NOT NULL                        COMMENT '主键（应用层雪花ID）',
  `tenant_id`       VARCHAR(32)     NOT NULL                        COMMENT '租户ID',
  `order_no`        VARCHAR(64)     NOT NULL                        COMMENT '订单号',
  `org_id`          BIGINT UNSIGNED NOT NULL                        COMMENT '归属组织',
  `house_id`        BIGINT UNSIGNED NOT NULL                        COMMENT '房源ID',
  `space_id`        BIGINT UNSIGNED          DEFAULT NULL           COMMENT '空间ID',
  `source_channel`  VARCHAR(30)     NOT NULL DEFAULT 'DIRECT'       COMMENT '来源渠道：DIRECT 直客 / OTA 携程美团 / WECHAT 微信小程序 / PHONE 电话 / WALKIN 上门 / OTHER 其他',
  `guest_name`      VARCHAR(64)     NOT NULL                        COMMENT '住客姓名（网约房必须实名）',
  `guest_phone`     VARCHAR(64)              DEFAULT NULL           COMMENT '住客手机号',
  `guest_id_card`   VARCHAR(128)             DEFAULT NULL           COMMENT '证件号（加密存储，网约房实名登记要求）',
  `guest_count`     INT             NOT NULL DEFAULT 1              COMMENT '入住人数',
  `check_in_time`   DATETIME(3)     NOT NULL                        COMMENT '入住时刻（精确到时分）',
  `check_out_time`  DATETIME(3)     NOT NULL                        COMMENT '退房时刻（精确到时分）',
  `night_count`     INT             NOT NULL                        COMMENT '房晚数（按日期差左闭右开；同日退房按 1 晚钟点房计）',
  `room_amount`     DECIMAL(14,2)   NOT NULL DEFAULT 0.00           COMMENT '房费（单价 × 房晚）',
  `extra_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0.00           COMMENT '其他费用（加床/清洁/超时等）',
  `discount_amount` DECIMAL(14,2)   NOT NULL DEFAULT 0.00           COMMENT '优惠金额',
  `total_amount`    DECIMAL(14,2)   NOT NULL DEFAULT 0.00           COMMENT '订单总额 = 房费 + 其他 - 优惠',
  `paid_amount`     DECIMAL(14,2)   NOT NULL DEFAULT 0.00           COMMENT '已付金额',
  `order_status`    VARCHAR(30)     NOT NULL DEFAULT 'PENDING'      COMMENT '状态：PENDING 待确认 / CONFIRMED 已确认 / CHECKED_IN 已入住 / CHECKED_OUT 已退房 / CANCELLED 已取消 / NO_SHOW 未到',
  `pay_status`      VARCHAR(20)     NOT NULL DEFAULT 'UNPAID'       COMMENT '支付状态：UNPAID 未付 / PAID 已付 / REFUNDED 已退',
  `cancel_reason`   VARCHAR(500)             DEFAULT NULL           COMMENT '取消原因',
  `remark`          VARCHAR(500)             DEFAULT NULL           COMMENT '备注',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0              COMMENT '逻辑删除：0 否 1 是',
  `create_by`       VARCHAR(64)              DEFAULT NULL           COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL                        COMMENT '创建时间',
  `update_by`       VARCHAR(64)              DEFAULT NULL           COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL                        COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_order_no` (`tenant_id`, `order_no`, `is_deleted`),
  KEY `idx_tenant_house_time` (`tenant_id`, `house_id`, `check_in_time`),
  KEY `idx_tenant_org_status` (`tenant_id`, `org_id`, `order_status`),
  KEY `idx_tenant_guest_phone` (`tenant_id`, `guest_phone`),
  KEY `idx_tenant_checkout` (`tenant_id`, `check_out_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='短租订单（酒店/民宿/网约房，时刻级租期）';
