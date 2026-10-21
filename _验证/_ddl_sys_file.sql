-- 附件表：承诺书、证件照片、报修照片、审批附件
-- 采用「元数据入库 + 文件落盘」方案：DB 只存索引，文件在 storage_dir 下
CREATE TABLE IF NOT EXISTS `bp_sys_file` (
  `id`            BIGINT        NOT NULL                COMMENT '主键',
  `tenant_id`     VARCHAR(32)   NOT NULL                COMMENT '租户ID',
  `file_name`     VARCHAR(255)  NOT NULL                COMMENT '原始文件名',
  `file_key`      VARCHAR(128)  NOT NULL                COMMENT '存储键（唯一，防重名）',
  `file_size`     BIGINT        NOT NULL DEFAULT 0      COMMENT '字节数',
  `content_type`  VARCHAR(128)                          COMMENT 'MIME 类型',
  `file_ext`      VARCHAR(20)                           COMMENT '扩展名',
  `biz_type`      VARCHAR(40)                           COMMENT '业务类型：APPLICATION/CONTRACT/WORKORDER/VERIFY',
  `biz_id`        BIGINT                                COMMENT '关联业务单据ID',
  `storage_type`  VARCHAR(20)   NOT NULL DEFAULT 'LOCAL' COMMENT '存储方式：LOCAL/S3/OSS',
  `storage_path`  VARCHAR(500)  NOT NULL                COMMENT '存储路径或对象键',
  `sha256`        VARCHAR(64)                           COMMENT '内容摘要（去重与完整性校验）',
  `uploader_id`   BIGINT                                COMMENT '上传人',
  `uploader_name` VARCHAR(64)                           COMMENT '上传人姓名',
  `is_deleted`    TINYINT(1)    NOT NULL DEFAULT 0      COMMENT '逻辑删除：0否 1是',
  `create_time`   DATETIME(3)   NOT NULL                COMMENT '上传时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_file_key` (`file_key`),
  KEY `idx_tenant_biz` (`tenant_id`, `biz_type`, `biz_id`),
  KEY `idx_tenant_time` (`tenant_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统附件表';
