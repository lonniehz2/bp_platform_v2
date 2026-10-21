-- =====================================================================
--  云门道业务平台 —— 数据库设计（第三轮）
--  第 2 部分：BC-03 人员与档案（9 表）  +  BC-04 权益与钥匙（7 表）= 16 表
--  目标库：MySQL 8.0+  /  InnoDB  /  utf8mb4
-- =====================================================================

SET NAMES utf8mb4;
USE `bp_platform`;


-- =====================================================================
--  BC-03  人员与档案（person）
-- =====================================================================

-- 3.1 人员主档（统一"人"，各场景术语不同但实体唯一）
CREATE TABLE `bp_person` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_code`    VARCHAR(64)     NOT NULL COMMENT '人员编号（租户内唯一）',
  `person_name`    VARCHAR(64)     NOT NULL COMMENT '姓名',
  `real_name`      VARCHAR(64)     NULL     COMMENT '实名姓名（实名认证后回填）',
  `phone`          VARCHAR(64)     NULL     COMMENT '手机号（加密存储）',
  `phone_hash`     VARCHAR(64)     NULL     COMMENT '手机号哈希（精确检索）',
  `id_card`        VARCHAR(128)    NULL     COMMENT '身份证号（加密存储）',
  `id_card_hash`   VARCHAR(64)     NULL     COMMENT '身份证号哈希（精确检索，唯一性校验）',
  `id_card_mask`   VARCHAR(32)     NULL     COMMENT '身份证号脱敏（展示用 330106********1219）',
  `gender`         VARCHAR(10)     NULL     COMMENT '性别：M / F / U 未知',
  `birthday`       DATE            NULL     COMMENT '出生日期',
  `nation`         VARCHAR(32)     NULL     COMMENT '民族',
  `native_place`   VARCHAR(128)    NULL     COMMENT '籍贯',
  `household_type` VARCHAR(30)     NULL     COMMENT '户籍类型：URBAN 城镇 / RURAL 农村 / OTHER',
  `household_addr` VARCHAR(255)    NULL     COMMENT '户籍地址',
  `marital_status` VARCHAR(20)     NULL     COMMENT '婚姻状况：SINGLE / MARRIED / DIVORCED / WIDOWED',
  `education`      VARCHAR(30)     NULL     COMMENT '学历（人才公寓场景用）',
  `title`          VARCHAR(64)     NULL     COMMENT '职称（人才公寓场景用）',
  `employer`       VARCHAR(128)    NULL     COMMENT '工作单位',
  `health_status`  VARCHAR(30)     NULL     COMMENT '健康状况',
  `person_source`  VARCHAR(30)     NOT NULL DEFAULT 'SELF' COMMENT '来源：SELF 自助注册 / ADMIN 后台录入 / IMPORT 导入 / HR_SYNC HR同步 / GOV_SYNC 政务同步',
  `org_id`         BIGINT UNSIGNED NULL     COMMENT '归属组织',
  -- 实名与绑定
  `verify_status`  VARCHAR(30)     NOT NULL DEFAULT 'UNVERIFIED' COMMENT '实名状态：UNVERIFIED 未认证 / VERIFIED 已认证 / FAILED 认证失败 / EXPIRED 已过期',
  `verify_time`    DATETIME(3)     NULL     COMMENT '实名认证时间',
  `verify_level`   VARCHAR(30)     NULL     COMMENT '实名等级：PERSONAL 个人实名 / ORG 组织内实名 / NONE 未实名',
  `bind_device_id` VARCHAR(128)    NULL     COMMENT '唯一性绑定设备标识（换手机需重新刷脸绑定）',
  `bind_id_card_hash` VARCHAR(64)  NULL     COMMENT '唯一性绑定身份证哈希（换证需重新绑定）',
  -- 状态
  `person_status`  VARCHAR(30)     NOT NULL DEFAULT 'NORMAL' COMMENT '人员状态：NORMAL 正常 / BLACKLIST 黑名单 / CANCELLED 已注销',
  `avatar_url`     VARCHAR(500)    NULL     COMMENT '人脸照片URL',
  `privacy_flag`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '隐私保护：1 是 0 否',
  `remark`         VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`      VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_personcode` (`tenant_id`,`person_code`,`is_deleted`),
  KEY `idx_tenant_idcard` (`tenant_id`,`id_card_hash`),
  KEY `idx_tenant_phone` (`tenant_id`,`phone_hash`),
  KEY `idx_tenant_org` (`tenant_id`,`org_id`,`person_status`),
  KEY `idx_tenant_verify` (`tenant_id`,`verify_status`),
  KEY `idx_bind_device` (`tenant_id`,`bind_device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人员主档（统一"人"实体）';

-- 3.2 保障对象档案（保障房专有扩展，与人员一对一）
CREATE TABLE `bp_person_guarantee_profile` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`        BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `security_type`    VARCHAR(30)     NOT NULL COMMENT '保障类型：PUBLIC 公租房 / AFFORDABLE 保租房 / TALENT 人才公寓 / LOW_RENT 廉租',
  -- 家庭与收入
  `family_size`      INT             NOT NULL DEFAULT 1 COMMENT '家庭人口数',
  `family_type`      VARCHAR(30)     NULL     COMMENT '家庭类型：SINGLE 单身 / COUPLE 双人 / WITH_CHILD 带子女 / WITH_ELDER 带老人 / OTHER',
  `monthly_income`   DECIMAL(14,2)   NULL     COMMENT '家庭月收入（元）',
  `income_level`     VARCHAR(30)     NULL     COMMENT '收入档位：LOW 低保 / LOW_INCOME 低收入 / MIDDLE_LOW 中低收入 / NORMAL 普通',
  `asset_declare`    DECIMAL(14,2)   NULL     COMMENT '申报财产（元）',
  `has_house`        TINYINT(1)      NULL     COMMENT '是否名下有房：0 无 1 有',
  `house_count`      INT             NULL     COMMENT '名下房产套数',
  `has_vehicle`      TINYINT(1)      NULL     COMMENT '是否有车',
  `social_security`  VARCHAR(30)     NULL     COMMENT '社保状况',
  -- 优先条件（打分用）
  `priority_flags`   VARCHAR(255)    NULL     COMMENT '优先条件（多选，逗号分隔）：DISABLED 残疾 / MARTYR 优抚 / MODEL 劳模 / HERO 见义勇为 / ELDER 孤寡老人 / FAMILY_PLAN 计生特殊 / TALENT 人才 / OTHER',
  `priority_score`   DECIMAL(8,2)    NULL     COMMENT '优先附加分',
  -- 人才公寓专用
  `talent_level`     VARCHAR(30)     NULL     COMMENT '人才层次：A/B/C/D 或 国家级/省级/市级/区级',
  `talent_cert_no`   VARCHAR(64)     NULL     COMMENT '人才认定证书编号',
  `talent_valid_to`  DATE            NULL     COMMENT '人才认定有效期',
  -- 状态
  `profile_status`   VARCHAR(30)     NOT NULL DEFAULT 'APPLICANT' COMMENT '档案状态：APPLICANT 申请中 / UNDER_REVIEW 审核中 / QUALIFIED 已通过 / IN_RESIDENCE 在保 / EXITED 已退出 / DISQUALIFIED 不合格',
  `qualify_date`     DATE            NULL     COMMENT '资格取得日期',
  `qualify_expire`   DATE            NULL     COMMENT '资格有效期至（年审用）',
  `first_apply_date` DATE            NULL     COMMENT '首次申请日期',
  `last_review_date` DATE            NULL     COMMENT '最近复核日期',
  `exit_date`        DATE            NULL     COMMENT '退出日期',
  `exit_reason`      VARCHAR(255)    NULL     COMMENT '退出原因',
  `remark`           VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`        VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_status` (`tenant_id`,`profile_status`),
  KEY `idx_tenant_type_status` (`tenant_id`,`security_type`,`profile_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='保障对象档案（保障房专有扩展）';

-- 3.3 家庭成员
CREATE TABLE `bp_person_family` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`      BIGINT UNSIGNED NOT NULL COMMENT '主申请人人员ID',
  `member_person_id` BIGINT UNSIGNED NULL   COMMENT '家庭成员人员ID（已建档时关联）',
  `member_name`    VARCHAR(64)     NOT NULL COMMENT '成员姓名',
  `member_id_card` VARCHAR(128)    NULL     COMMENT '成员身份证号（加密）',
  `member_id_card_hash` VARCHAR(64) NULL     COMMENT '成员身份证号哈希',
  `relation`       VARCHAR(30)     NOT NULL COMMENT '与主申请人关系：SPOUSE 配偶 / CHILD 子女 / PARENT 父母 / SIBLING 兄弟姐妹 / OTHER',
  `gender`         VARCHAR(10)     NULL COMMENT '性别：M 男 / F 女 / U 未知',
  `birthday`       DATE            NULL COMMENT '出生日期',
  `is_co_applicant` TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否共同申请人',
  `is_cohabitant`  TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否共同居住',
  `verify_status`  VARCHAR(30)     NULL     COMMENT '核验状态',
  `sort_no`        INT             NOT NULL DEFAULT 0 COMMENT '排序号',
  `is_deleted`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`      VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_member` (`tenant_id`,`member_person_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='家庭成员';

-- 3.4 证件与材料
CREATE TABLE `bp_person_document` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`     BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `doc_type`      VARCHAR(40)     NOT NULL COMMENT '证件类型：ID_CARD 身份证 / HOUSEHOLD 户口本 / RESIDENCE 居住证 / LOW_INCOME 低保证 / DISABILITY 残疾证 / MARRIAGE 结婚证 / INCOME_PROOF 收入证明 / HOUSE_PROOF 房产证明 / TALENT_CERT 人才证书 / EMPLOYMENT 劳动合同 / OTHER',
  `doc_no`        VARCHAR(128)    NULL     COMMENT '证件号码',
  `doc_name`      VARCHAR(128)    NULL     COMMENT '证件名称/文件名',
  `file_url`      VARCHAR(500)    NULL     COMMENT '文件URL（正面）',
  `file_url_back` VARCHAR(500)    NULL     COMMENT '文件URL（反面）',
  `issue_org`     VARCHAR(128)    NULL     COMMENT '签发机关',
  `issue_date`    DATE            NULL     COMMENT '签发日期',
  `expire_date`   DATE            NULL     COMMENT '有效期至',
  `verify_status` VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '核验状态：PENDING 待核验 / VERIFIED 已核验 / FAILED 核验失败',
  `verify_time`   DATETIME(3)     NULL COMMENT '核验/认证时间',
  `verify_remark` VARCHAR(500)    NULL COMMENT '核验备注',
  `source_type`   VARCHAR(30)     NULL     COMMENT '来源：UPLOAD 上传 / OCR 识别 / GOV_SYNC 政务同步',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_person_type` (`tenant_id`,`person_id`,`doc_type`),
  KEY `idx_tenant_expire` (`tenant_id`,`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='证件与材料';

-- 3.5 人员标签
CREATE TABLE `bp_person_tag` (
  `id`         BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`  VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `tag_code`   VARCHAR(64)     NOT NULL COMMENT '标签编码',
  `tag_name`   VARCHAR(64)     NOT NULL COMMENT '标签名称',
  `tag_group`  VARCHAR(30)     NULL     COMMENT '标签分组',
  `tag_color`  VARCHAR(20)     NULL     COMMENT '标签颜色',
  `sort_no`    INT             NOT NULL DEFAULT 0 COMMENT '排序号',
  `status`     VARCHAR(20)     NOT NULL DEFAULT 'ENABLED' COMMENT '状态：ENABLED 启用 / DISABLED 停用',
  `is_deleted` TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_time` DATETIME(3)    NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_tagcode` (`tenant_id`,`tag_code`,`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人员标签定义';

CREATE TABLE `bp_person_tag_relation` (
  `id`          BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`   VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`   BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `tag_id`      BIGINT UNSIGNED NOT NULL COMMENT '标签ID',
  `create_by`   VARCHAR(64)     NULL COMMENT '创建人',
  `create_time` DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_person_tag` (`tenant_id`,`person_id`,`tag_id`),
  KEY `idx_tag` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人员-标签关系';

-- 3.6 黑名单 / 失信名单
CREATE TABLE `bp_person_blacklist` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`     BIGINT UNSIGNED NULL     COMMENT '人员ID',
  `id_card_hash`  VARCHAR(64)     NULL     COMMENT '身份证哈希（未建档人员也能拉黑）',
  `person_name`   VARCHAR(64)     NULL     COMMENT '姓名',
  `list_type`     VARCHAR(30)     NOT NULL DEFAULT 'BLACKLIST' COMMENT '名单类型：BLACKLIST 黑名单 / DISHONEST 失信 / WARNING 关注',
  `reason_type`   VARCHAR(40)     NULL     COMMENT '原因类型：SUBLEASE 转租转借 / ARREARS 欠费 / VIOLATION 违规违约 / FALSE_MATERIAL 虚假材料 / OTHER',
  `reason`        VARCHAR(500)    NULL     COMMENT '原因说明',
  `evidence_url`  VARCHAR(1000)   NULL     COMMENT '证据附件（逗号分隔）',
  `start_date`    DATE            NOT NULL COMMENT '生效日期',
  `end_date`      DATE            NULL     COMMENT '失效日期（NULL 长期）',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE 生效 / RELEASED 已解除',
  `release_reason` VARCHAR(500)   NULL COMMENT '解除原因',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`,`status`),
  KEY `idx_tenant_idcard` (`tenant_id`,`id_card_hash`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='黑名单/失信名单';

-- 3.7 实名认证记录（调用 IoT §9 的留痕，用于合规举证）
CREATE TABLE `bp_person_verify_record` (
  `id`             BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`      VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`      BIGINT UNSIGNED NULL     COMMENT '人员ID',
  `verify_type`    VARCHAR(30)     NOT NULL COMMENT '认证类型：PERSONAL 个人实名 / ORG 组织实名 / FACE_COMPARE 人脸比对 / IDCARD_DECODE 身份证解码',
  `user_name`      VARCHAR(64)     NULL     COMMENT '提交的姓名（加密）',
  `id_card_hash`   VARCHAR(64)     NULL     COMMENT '身份证哈希',
  `face_img_url`   VARCHAR(500)    NULL     COMMENT '人脸照片URL',
  `idcard_img_url` VARCHAR(500)    NULL     COMMENT '身份证照片URL',
  `request_no`     VARCHAR(64)     NULL     COMMENT '请求流水号',
  `command_id`     VARCHAR(64)     NULL     COMMENT 'IoT commandId（如 E755B3AB842F4A22331985D5D01D34E 实名认证）',
  `response_code`  VARCHAR(20)     NULL     COMMENT '响应码（100 成功）',
  `result_code`    VARCHAR(20)     NULL     COMMENT '结果码：1 查询成功 / 0 查无结果',
  `face_score`     DECIMAL(8,2)    NULL     COMMENT '人照匹配分数',
  `face_result`    VARCHAR(10)     NULL     COMMENT '人脸结果：0 null / 1 同一人 / 2 不同人 / 3 不能确定 / 4 无法比对 / 5 库中无照片',
  `citizen_result` VARCHAR(10)     NULL     COMMENT '身份核查：1 一致 / 2 不一致 / 3 库中无此号',
  `verify_pass`    TINYINT(1)      NULL     COMMENT '是否通过：1 是 0 否',
  `fail_reason`    VARCHAR(500)    NULL     COMMENT '失败原因',
  `raw_response`   JSON            NULL     COMMENT '原始响应（留痕）',
  `create_time`    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`,`create_time`),
  KEY `idx_request` (`request_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实名认证记录（合规留痕）';


-- =====================================================================
--  BC-04  权益与钥匙（grant）
-- =====================================================================

-- 4.1 权益（四级权限：所有权/管理权/使用权/访客权）
CREATE TABLE `bp_grant_entitlement` (
  `id`               BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`        VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `grant_no`         VARCHAR(64)     NOT NULL COMMENT '权益编号',
  `grant_level`      VARCHAR(30)     NOT NULL COMMENT '权限层级：OWNERSHIP 所有权 / MANAGEMENT 管理权 / USAGE 使用权 / VISITOR 访客权',
  -- 主体
  `holder_type`      VARCHAR(20)     NOT NULL DEFAULT 'PERSON' COMMENT '持有者类型：PERSON 人员 / ORG 组织',
  `person_id`        BIGINT UNSIGNED NULL     COMMENT '人员ID',
  `org_id`           BIGINT UNSIGNED NULL     COMMENT '组织ID（组织级权益）',
  -- 客体（空间）
  `space_id`         BIGINT UNSIGNED NOT NULL COMMENT '空间ID（权限锚点，向下自动继承）',
  `space_path`       VARCHAR(1000)   NOT NULL DEFAULT '' COMMENT '空间路径快照（继承计算用）',
  `house_id`         BIGINT UNSIGNED NULL     COMMENT '房源ID（如为房源级权益）',
  -- 有效期
  `valid_start`      DATETIME(3)     NOT NULL COMMENT '生效时间',
  `valid_end`        DATETIME(3)     NULL     COMMENT '失效时间（NULL 永久，仅所有权可永久）',
  -- 权限内容
  `allow_open`       TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否含开门权限（所有权为 0）',
  `allow_manage`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否含管理权限',
  `allow_delegate`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否可转授（所有权可转让管理权）',
  `visit_limit_times` INT            NULL     COMMENT '访客权次数限制（NULL 不限）',
  `visit_used_times`  INT            NOT NULL DEFAULT 0 COMMENT '访客权已用次数',
  -- 来源与状态
  `source_type`      VARCHAR(30)     NOT NULL COMMENT '来源：CONTRACT 合同 / TRANSFER 转让 / DELEGATE 授权 / INHERIT 继承 / MANUAL 手工',
  `source_id`        BIGINT UNSIGNED NULL     COMMENT '来源单据ID（合同/转让单）',
  `parent_grant_id`  BIGINT UNSIGNED NULL     COMMENT '上级权益ID（继承关系）',
  `grant_status`     VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待生效 / EFFECTIVE 已生效 / EXPIRED 已到期 / REVOKED 已撤销 / FROZEN 已冻结',
  `freeze_reason`    VARCHAR(500)    NULL     COMMENT '冻结原因（欠费/违规）',
  `revoke_reason`    VARCHAR(500)    NULL     COMMENT '撤销原因',
  `remark`           VARCHAR(500)    NULL COMMENT '备注',
  `is_deleted`       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`        VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`        VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_grantno` (`tenant_id`,`grant_no`),
  KEY `idx_tenant_person_status` (`tenant_id`,`person_id`,`grant_status`),
  KEY `idx_tenant_space_status` (`tenant_id`,`space_id`,`grant_status`),
  KEY `idx_tenant_level` (`tenant_id`,`grant_level`,`grant_status`),
  KEY `idx_tenant_valid_end` (`tenant_id`,`valid_end`),
  KEY `idx_parent` (`parent_grant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权益（四级权限）';

-- 4.2 钥匙包（以人为中心的介质集合）
CREATE TABLE `bp_grant_keyring` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`     BIGINT UNSIGNED NOT NULL COMMENT '所属人员',
  `key_type`      VARCHAR(30)     NOT NULL COMMENT '钥匙类型：FACE 人脸 / FINGERPRINT 指纹 / PALM_VEIN 掌静脉 / PASSWORD 密码 / TEMP_PASSWORD 临时密码 / DURESS_PASSWORD 挟持码 / VISITOR_PASSWORD 访客码 / IC_CARD IC卡 / ID_CARD 身份证 / NFC 手机NFC / BLUETOOTH 蓝牙 / APP APP授权',
  `key_class`     VARCHAR(30)     NOT NULL COMMENT '钥匙分类（四分类）：PERSONAL_REAL 个人实名 / PERSONAL_UNREAL 个人非实名 / ORG_REAL 组织内实名 / ORG_UNREAL 组织内非实名',
  `key_alias`     VARCHAR(128)    NULL     COMMENT '别名（如"右手大拇指""右掌"）',
  `channel_module_type` VARCHAR(10) NULL    COMMENT '介质模块类型：00 蓝牙 / 01 键盘 / 02 刷卡 / 03 红外 / 04 指纹 / 05 掌静脉 / 06 人脸 / 07 内部',
  `channel_type`  VARCHAR(10)     NULL     COMMENT '介质类型编码（401 管理指纹 / 404 普通指纹 / 601 人脸等，对应 IoT §8.3.4）',
  `channel_value` VARCHAR(512)    NULL     COMMENT '介质值（卡号/密码密文/指纹模板，加密）',
  `channel_value2` VARCHAR(512)   NULL     COMMENT '介质值2',
  `key_source`    VARCHAR(30)     NOT NULL COMMENT '录入来源：SELF_APP 自助录入 / ADMIN 后台录入 / IDCARD 身份证下发 / IMPORT 导入',
  `verify_way`    VARCHAR(30)     NULL     COMMENT '验证方式：FACE_VERIFY 人证核验 / ORG_VERIFY 组织实名 / NONE 无',
  `is_real`       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否实名介质：1 强安全 0 弱安全',
  `sync_scope`    VARCHAR(30)     NOT NULL DEFAULT 'ALL_GRANTED' COMMENT '同步范围：ALL_GRANTED 已授权全部设备 / SPECIFIC 指定设备',
  `key_status`    VARCHAR(30)     NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE 正常 / FROZEN 已冻结 / DELETED 已删除 / EXPIRED 已过期',
  `expire_time`   DATETIME(3)     NULL     COMMENT '有效期（密码类）',
  `is_deleted`    TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  `create_by`     VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`     VARCHAR(64)     NULL COMMENT '更新人',
  `update_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`,`key_status`),
  KEY `idx_tenant_type` (`tenant_id`,`key_type`,`key_status`),
  KEY `idx_tenant_class` (`tenant_id`,`key_class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='钥匙包（以人为中心的介质集合）';

-- 4.3 授权任务（下发到 IoT 的编排记录）
CREATE TABLE `bp_grant_task` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `task_no`         VARCHAR(64)     NOT NULL COMMENT '任务编号',
  `idempotent_key`  VARCHAR(128)    NOT NULL COMMENT '幂等键（sha1(personId+spaceId+level+有效期)）',
  `task_type`       VARCHAR(30)     NOT NULL COMMENT '任务类型：GRANT 授权 / REVOKE 撤销 / FREEZE 冻结 / UNFREEZE 解冻 / SYNC 同步',
  `person_id`       BIGINT UNSIGNED NULL     COMMENT '目标人员',
  `entitlement_id`  BIGINT UNSIGNED NULL     COMMENT '关联权益ID',
  `keyring_ids`     VARCHAR(1000)   NULL     COMMENT '关联钥匙包ID（逗号分隔）',
  `lock_count`      INT             NOT NULL DEFAULT 0 COMMENT '涉及锁数量',
  `success_count`   INT             NOT NULL DEFAULT 0 COMMENT '成功数量',
  `fail_count`      INT             NOT NULL DEFAULT 0 COMMENT '失败数量',
  `valid_start`     DATETIME(3)     NULL     COMMENT '授权生效时间（透传 IoT）',
  `valid_end`       DATETIME(3)     NULL     COMMENT '授权失效时间（透传 IoT）',
  `iot_task_id`     VARCHAR(128)    NULL     COMMENT 'IoT 异步任务ID（syncTask/result/list 查询用）',
  `iot_request_no`  VARCHAR(64)     NULL     COMMENT 'IoT 请求流水号',
  `task_status`     VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING 待下发 / DISPATCHING 下发中 / SUCCESS 成功 / PARTIAL 部分成功 / FAILED 失败 / MANUAL 转人工',
  `retry_count`     INT             NOT NULL DEFAULT 0 COMMENT '重试次数',
  `last_error`      VARCHAR(1000)   NULL     COMMENT '最近错误',
  `trigger_source`  VARCHAR(30)     NOT NULL COMMENT '触发来源：CONTRACT 合同生效 / KEYRING_ADD 新增钥匙 / SPACE_CHANGE 空间变更 / MANUAL 手工 / RECONCILE 对账修正',
  `create_by`       VARCHAR(64)     NULL COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `dispatch_time`   DATETIME(3)     NULL     COMMENT '下发时间',
  `finish_time`     DATETIME(3)     NULL     COMMENT '完成时间',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_taskno` (`tenant_id`,`task_no`),
  UNIQUE KEY `uk_idempotent` (`tenant_id`,`idempotent_key`,`task_type`),
  KEY `idx_tenant_status` (`tenant_id`,`task_status`,`create_time`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_iot_task` (`iot_task_id`),
  KEY `idx_dispatch` (`task_status`,`dispatch_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='授权任务（IoT 下发编排记录）';

-- 4.4 授权任务明细（逐锁结果）
CREATE TABLE `bp_grant_task_detail` (
  `id`           BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`    VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `task_id`      BIGINT UNSIGNED NOT NULL COMMENT '任务ID',
  `device_id`    VARCHAR(64)     NOT NULL COMMENT '设备ID',
  `device_mac`   VARCHAR(64)     NULL     COMMENT '设备MAC',
  `lock_id`      VARCHAR(64)     NULL     COMMENT 'IoT 侧门锁ID',
  `space_id`     BIGINT UNSIGNED NULL     COMMENT '所属空间',
  `keyring_id`   BIGINT UNSIGNED NULL     COMMENT '使用的钥匙包介质',
  `detail_status` VARCHAR(30)    NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING / SUCCESS / FAILED / SKIPPED',
  `error_code`   VARCHAR(40)     NULL     COMMENT '错误码（IoT 错误码，如 99990001）',
  `error_msg`    VARCHAR(500)    NULL     COMMENT '错误信息',
  `duration_ms`  INT             NULL     COMMENT '耗时（毫秒）',
  `create_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_task` (`task_id`,`detail_status`),
  KEY `idx_tenant_device` (`tenant_id`,`device_id`),
  KEY `idx_tenant_lock` (`lock_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='授权任务明细（逐锁结果）';

-- 4.5 授权对账差异记录
CREATE TABLE `bp_grant_reconcile_diff` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `device_id`       VARCHAR(64)     NOT NULL COMMENT '设备ID',
  `lock_id`         VARCHAR(64)     NULL     COMMENT 'IoT 门锁ID',
  `person_id`       BIGINT UNSIGNED NULL     COMMENT '人员ID',
  `target_user_mobile` VARCHAR(64)  NULL     COMMENT 'IoT 侧授权对象账号',
  `diff_type`       VARCHAR(30)     NOT NULL COMMENT '差异类型：LOCAL_MISSING 本地应有IoT无 / IOT_EXTRA IoT有本地无 / PERIOD_MISMATCH 有效期不一致 / MEDIA_MISMATCH 介质不一致',
  `local_value`     VARCHAR(500)    NULL     COMMENT '本地值',
  `iot_value`       VARCHAR(500)    NULL     COMMENT 'IoT 值',
  `handle_action`   VARCHAR(30)     NULL     COMMENT '处置动作：REGRANT 重新授权 / REVOKE 撤销 / MANUAL 人工 / IGNORED 忽略',
  `handle_status`   VARCHAR(20)     NOT NULL DEFAULT 'PENDING' COMMENT '处置状态：PENDING / HANDLED / IGNORED',
  `handle_time`     DATETIME(3)     NULL COMMENT '处置时间',
  `handle_remark`   VARCHAR(500)    NULL COMMENT '处置备注',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`handle_status`,`create_time`),
  KEY `idx_tenant_device` (`tenant_id`,`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='授权对账差异记录';

-- 4.6 IoT 人员映射（本地人员 ↔ IoT 人员 ownerId）
CREATE TABLE `bp_grant_iot_person_map` (
  `id`                BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`         VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`         BIGINT UNSIGNED NOT NULL COMMENT '本地人员ID',
  `iot_owner_id`      VARCHAR(64)     NULL     COMMENT 'IoT 人员主键 ownerId',
  `iot_organ_id`      VARCHAR(64)     NULL     COMMENT 'IoT 组织ID',
  `iot_account`       VARCHAR(64)     NOT NULL COMMENT 'IoT 侧人员账号（手机号）',
  `sync_status`       VARCHAR(20)     NOT NULL DEFAULT 'SYNCED' COMMENT '同步状态：SYNCED / PENDING / FAILED',
  `sync_time`         DATETIME(3)     NULL     COMMENT '最近同步时间',
  `create_time`       DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_time`       DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_owner` (`tenant_id`,`iot_owner_id`),
  KEY `idx_tenant_account` (`tenant_id`,`iot_account`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IoT 人员映射（本地 ↔ ownerId）';

-- 4.7 授权操作审计
CREATE TABLE `bp_grant_audit_log` (
  `id`            BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`     VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `biz_type`      VARCHAR(30)     NOT NULL COMMENT '业务类型：GRANT / REVOKE / FREEZE / UNFREEZE / TRANSFER / DELEGATE',
  `biz_id`        BIGINT UNSIGNED NULL     COMMENT '业务单据ID',
  `person_id`     BIGINT UNSIGNED NULL     COMMENT '被操作人员',
  `space_id`      BIGINT UNSIGNED NULL     COMMENT '涉及空间',
  `operator_id`   BIGINT UNSIGNED NULL     COMMENT '操作人',
  `operator_name` VARCHAR(64)     NULL COMMENT '操作人姓名',
  `reason`        VARCHAR(500)    NULL     COMMENT '操作依据/原因',
  `before_json`   JSON            NULL     COMMENT '变更前',
  `after_json`    JSON            NULL     COMMENT '变更后',
  `result`        VARCHAR(20)     NULL     COMMENT '结果：SUCCESS / FAILED',
  `create_time`   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_time` (`tenant_id`,`create_time`),
  KEY `idx_tenant_person` (`tenant_id`,`person_id`),
  KEY `idx_tenant_space` (`tenant_id`,`space_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='授权操作审计（不可修改）';


-- 3.9 送达地址（政策扩展 C8：成都§34 法律文书送达；变更未告知的原地址视为有效）
CREATE TABLE `bp_person_service_address` (
  `id`              BIGINT UNSIGNED NOT NULL COMMENT '主键',
  `tenant_id`       VARCHAR(32)     NOT NULL COMMENT '租户ID',
  `person_id`       BIGINT UNSIGNED NOT NULL COMMENT '人员ID',
  `address_type`    VARCHAR(30)     NOT NULL DEFAULT 'LEGAL' COMMENT '类型：LEGAL 法律文书送达 / MAIL 通讯 / RESIDENCE 居住',
  `consignee_name`  VARCHAR(64)     NOT NULL COMMENT '收件人姓名',
  `consignee_phone` VARCHAR(32)     NOT NULL COMMENT '收件人电话',
  `province_code`   VARCHAR(12)     NULL     COMMENT '省级区划码',
  `city_code`       VARCHAR(12)     NULL     COMMENT '市级区划码',
  `district_code`   VARCHAR(12)     NULL     COMMENT '区县区划码',
  `detail_address`  VARCHAR(500)    NOT NULL COMMENT '详细地址',
  `postal_code`     VARCHAR(16)     NULL     COMMENT '邮政编码',
  `source`          VARCHAR(30)     NOT NULL DEFAULT 'DECLARED' COMMENT '来源：DECLARED 申报填写 / CONTRACT 合同填写 / SYSTEM 系统维护 / IMPORT 导入',
  `is_effective`    TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否为当前有效地址：1 是 0 否（政策：变更未主动告知的，原地址视为有效）',
  `effective_from`  DATETIME(3)     NOT NULL COMMENT '生效时间',
  `effective_to`    DATETIME(3)     NULL     COMMENT '失效时间',
  `confirm_status`  VARCHAR(20)     NOT NULL DEFAULT 'UNCONFIRMED' COMMENT '确认状态：UNCONFIRMED 未确认 / CONFIRMED 已确认（信息确认书）',
  `confirm_time`    DATETIME(3)     NULL     COMMENT '确认时间',
  `create_by`       VARCHAR(64)     NULL     COMMENT '创建人',
  `create_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `update_by`       VARCHAR(64)     NULL     COMMENT '更新人',
  `update_time`     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  `is_deleted`      TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '逻辑删除：0 否 1 是',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_person_type` (`tenant_id`,`person_id`,`address_type`,`is_effective`),
  KEY `idx_tenant_effective` (`tenant_id`,`is_effective`,`effective_from`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='送达地址（支撑法律文书送达）';


-- ---------------------------------------------------------------------
-- P2 完成：BC-03 人员与档案（9 表）、BC-04 权益与钥匙（7 表）= 16 表
-- 累计：30 表
-- ---------------------------------------------------------------------
