package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 系统附件。对应 `bp_sys_file`。
 *
 * <p>元数据入库、文件落盘：数据库只存索引，便于换存储（LOCAL/S3/OSS）
 * 而不影响业务表。
 */
@Data
@TableName("bp_sys_file")
public class SysFile {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String fileName;
    /** 存储键（唯一，防重名覆盖） */
    private String fileKey;
    private Long fileSize;
    private String contentType;
    private String fileExt;
    /** APPLICATION / CONTRACT / WORKORDER / VERIFY */
    private String bizType;
    private Long bizId;
    /** LOCAL / S3 / OSS */
    private String storageType;
    private String storagePath;
    /** 内容摘要（去重与完整性校验） */
    private String sha256;
    private Long uploaderId;
    private String uploaderName;

    @TableLogic
    private Integer isDeleted;

    private LocalDateTime createTime;
}
