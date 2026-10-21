-- =============================================================================
--  P6 · 短租日房态（支撑酒店/民宿/网约房按天售卖）
--  说明：长租（保障房/公寓/宿舍）以"房源整体状态"表达是否可租；
--        短租需要"按日"表达可售性，故新增日房态表。
--  关键约束：uk_tenant_house_date —— 同一房源同一天只能有一条有效记录，
--            从库层杜绝"同一天被卖两次"。
-- =============================================================================

CREATE TABLE `bp_asset_house_calendar` (
  `id`            BIGINT UNSIGNED NOT NULL                          COMMENT '主键（应用层雪花ID）',
  `tenant_id`     VARCHAR(32)     NOT NULL                          COMMENT '租户ID',
  `org_id`        BIGINT UNSIGNED NOT NULL                          COMMENT '归属组织',
  `house_id`      BIGINT UNSIGNED NOT NULL                          COMMENT '房源ID',
  `cal_date`      DATE            NOT NULL                          COMMENT '日期',
  `day_status`    VARCHAR(20)     NOT NULL DEFAULT 'AVAILABLE'      COMMENT '房态：AVAILABLE 可售 / BOOKED 已预订 / OCCUPIED 已入住 / CLOSED 停售 / MAINTENANCE 维修',
  `price_override` DECIMAL(14,2)           DEFAULT NULL             COMMENT '当日价（为空=用计费规则默认价，用于节假日调价）',
  `booking_id`    BIGINT UNSIGNED           DEFAULT NULL            COMMENT '占用单据ID（预订单/合同ID）',
  `source_type`   VARCHAR(20)              DEFAULT NULL             COMMENT '占用来源：BOOKING 预订 / CONTRACT 合同 / MANUAL 手工',
  `remark`        VARCHAR(500)             DEFAULT NULL             COMMENT '备注',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0                COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)              DEFAULT NULL             COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL                          COMMENT '创建时间',
  `update_by`     VARCHAR(64)              DEFAULT NULL             COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL                          COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_house_date` (`tenant_id`, `house_id`, `cal_date`, `is_deleted`),
  KEY `idx_tenant_org_date` (`tenant_id`, `org_id`, `cal_date`),
  KEY `idx_tenant_house_status` (`tenant_id`, `house_id`, `day_status`),
  KEY `idx_tenant_booking` (`tenant_id`, `booking_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='房源日房态（短租/民宿按天可售性）';
