# -*- coding: utf-8 -*-
"""补齐：文件上传后端（bp_sys_file）+ DDL 脚本"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
DDL = r'D:\Work\业务平台开发\_验证\_ddl_sys_file.sql'
F = {}

# ==================== DDL（回内网执行） ====================
DDL_SQL = '''-- 附件表：承诺书、证件照片、报修照片、审批附件
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
'''
io.open(DDL, 'w', encoding='utf-8').write(DDL_SQL)
print('  + DDL 脚本：%s' % DDL)

# ==================== 实体 ====================
F['sys/entity/SysFile.java'] = '''package com.yundao.bp.sys.entity;

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
'''

F['sys/mapper/SysFileMapper.java'] = '''package com.yundao.bp.sys.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.sys.entity.SysFile;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SysFileMapper extends BaseMapper<SysFile> {
}
'''

# ==================== 服务 ====================
F['sys/service/FileService.java'] = '''package com.yundao.bp.sys.service;

import com.yundao.bp.sys.entity.SysFile;
import java.io.InputStream;
import java.util.List;
import org.springframework.web.multipart.MultipartFile;

/**
 * 附件服务。
 *
 * <p><b>安全约束</b>（缺一不可）：
 * <ol>
 *   <li>扩展名白名单：只允许图片与 PDF（防上传 jsp/exe）</li>
 *   <li>大小上限：默认 10MB</li>
 *   <li>文件名重写为 UUID 存储键：<b>不信任用户文件名</b>，防目录穿越</li>
 *   <li>按租户 + 业务单据隔离查询</li>
 * </ol>
 */
public interface FileService {

    SysFile upload(MultipartFile file, String bizType, Long bizId,
                   Long uploaderId, String uploaderName);

    SysFile get(Long id);

    /** 取文件流（用于下载/预览）。 */
    InputStream openStream(Long id);

    List<SysFile> listByBiz(String bizType, Long bizId);

    /** 逻辑删除。 */
    void remove(Long id);
}
'''

F['sys/service/impl/FileServiceImpl.java'] = '''package com.yundao.bp.sys.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.entity.SysFile;
import com.yundao.bp.sys.mapper.SysFileMapper;
import com.yundao.bp.sys.service.FileService;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

/**
 * 附件实现（本地磁盘存储）。
 */
@Service
public class FileServiceImpl implements FileService {

    private static final Logger log = LoggerFactory.getLogger(FileServiceImpl.class);

    /** 扩展名白名单：图片与 PDF，禁止可执行脚本类 */
    private static final Set<String> ALLOWED_EXT = Set.of(
            "jpg", "jpeg", "png", "gif", "webp", "bmp", "pdf");
    /** 上限 10MB */
    private static final long MAX_SIZE = 10L * 1024 * 1024;

    private final SysFileMapper mapper;
    private final SnowflakeIdGenerator idGen;
    private final String storageDir;

    public FileServiceImpl(SysFileMapper mapper, SnowflakeIdGenerator idGen,
                           @Value("${bp.file.storage-dir:/tmp/bp-files}") String storageDir) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.storageDir = storageDir;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SysFile upload(MultipartFile file, String bizType, Long bizId,
                          Long uploaderId, String uploaderName) {
        if (file == null || file.isEmpty()) {
            throw BizException.paramInvalid("上传文件不能为空");
        }
        if (file.getSize() > MAX_SIZE) {
            throw BizException.paramInvalid(
                    "文件超过上限 " + (MAX_SIZE / 1024 / 1024) + "MB，当前 "
                            + (file.getSize() / 1024) + "KB");
        }
        String original = file.getOriginalFilename() == null ? "unknown"
                : Path.of(file.getOriginalFilename()).getFileName().toString();
        String ext = "";
        int dot = original.lastIndexOf('.');
        if (dot > 0) {
            ext = original.substring(dot + 1).toLowerCase();
        }
        if (!ALLOWED_EXT.contains(ext)) {
            throw BizException.paramInvalid(
                    "不支持的文件类型「" + ext + "」，仅允许："
                            + String.join("/", ALLOWED_EXT));
        }

        // 文件名重写为 UUID：不信任用户文件名，杜绝目录穿越
        String fileKey = UUID.randomUUID().toString().replace("-", "") + "." + ext;
        String day = LocalDate.now().toString();
        Path dir = Path.of(storageDir, day);
        Path target = dir.resolve(fileKey).normalize();
        // 双重校验：确保最终路径仍在本租户存储根目录内
        if (!target.startsWith(Path.of(storageDir).normalize())) {
            throw BizException.paramInvalid("非法存储路径");
        }
        try {
            Files.createDirectories(dir);
            try (InputStream in = file.getInputStream()) {
                Files.copy(in, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            log.error("文件落盘失败：{}", e.getMessage());
            throw new BizException(ErrorCode.SYSTEM_ERROR, "文件保存失败：" + e.getMessage());
        }

        String sha = null;
        try (InputStream in = Files.newInputStream(target)) {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) {
                md.update(buf, 0, n);
            }
            sha = HexFormat.of().formatHex(md.digest());
        } catch (Exception e) {
            log.warn("计算摘要失败（不影响上传）：{}", e.getMessage());
        }

        SysFile f = new SysFile();
        f.setId(idGen.nextId());
        f.setTenantId(TenantContext.tenantId());
        f.setFileName(original);
        f.setFileKey(fileKey);
        f.setFileSize(file.getSize());
        f.setContentType(file.getContentType());
        f.setFileExt(ext);
        f.setBizType(bizType);
        f.setBizId(bizId);
        f.setStorageType("LOCAL");
        f.setStoragePath(day + "/" + fileKey);
        f.setSha256(sha);
        f.setUploaderId(uploaderId);
        f.setUploaderName(uploaderName);
        f.setIsDeleted(0);
        f.setCreateTime(LocalDateTime.now());
        mapper.insert(f);
        log.info("附件已上传：{}（{}，{}KB，{}）", original, bizType,
                file.getSize() / 1024, fileKey);
        return f;
    }

    @Override
    public SysFile get(Long id) {
        SysFile f = mapper.selectById(id);
        if (f == null) {
            throw BizException.notFound("附件");
        }
        return f;
    }

    @Override
    public InputStream openStream(Long id) {
        SysFile f = get(id);
        Path p = Path.of(storageDir, f.getStoragePath()).normalize();
        if (!p.startsWith(Path.of(storageDir).normalize())) {
            throw BizException.paramInvalid("非法文件路径");
        }
        try {
            return Files.newInputStream(p);
        } catch (IOException e) {
            throw new BizException(ErrorCode.NOT_FOUND, "文件已丢失或不可读");
        }
    }

    @Override
    public List<SysFile> listByBiz(String bizType, Long bizId) {
        return mapper.selectList(new LambdaQueryWrapper<SysFile>()
                .eq(SysFile::getBizType, bizType)
                .eq(bizId != null, SysFile::getBizId, bizId)
                .orderByDesc(SysFile::getId));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void remove(Long id) {
        SysFile f = get(id);
        f.setIsDeleted(1);
        mapper.updateById(f);
        log.info("附件已逻辑删除：{}", f.getFileName());
    }
}
'''

# ==================== 控制器 ====================
F['sys/controller/FileController.java'] = '''package com.yundao.bp.sys.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.entity.SysFile;
import com.yundao.bp.sys.service.FileService;
import com.yundao.bp.sys.audit.Audit;
import java.io.InputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

/**
 * 附件接口（承诺书、证件、报修照片）。
 */
@RestController
@RequestMapping("/api/v1/files")
public class FileController {

    private final FileService service;

    public FileController(FileService service) {
        this.service = service;
    }

    /** ⭐ 上传（multipart/form-data）。 */
    @PostMapping("/upload")
    @Audit(type = "DATA", level = "IMPORTANT", action = "上传附件")
    public R<SysFile> upload(@RequestParam("file") MultipartFile file,
                             @RequestParam(required = false) String bizType,
                             @RequestParam(required = false) Long bizId) {
        LoginUser u = LoginUser.get();
        return R.ok(service.upload(file, bizType, bizId,
                u == null ? null : u.userId(),
                u == null ? null : (u.realName() == null ? u.username() : u.realName())));
    }

    /** 按业务单据列出附件。 */
    @GetMapping
    public R<List<SysFile>> list(@RequestParam String bizType,
                                 @RequestParam(required = false) Long bizId) {
        return R.ok(service.listByBiz(bizType, bizId));
    }

    /** ⭐ 下载/预览（浏览器内联展示图片）。 */
    @GetMapping("/{id}/download")
    public ResponseEntity<InputStreamResource> download(@PathVariable Long id) {
        SysFile f = service.get(id);
        InputStream in = service.openStream(id);
        String encoded = URLEncoder.encode(f.getFileName(), StandardCharsets.UTF_8)
                .replace("+", "%20");
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "inline; filename*=UTF-8''" + encoded)
                .contentType(f.getContentType() == null
                        ? MediaType.APPLICATION_OCTET_STREAM
                        : MediaType.parseMediaType(f.getContentType()))
                .contentLength(f.getFileSize() == null ? 0 : f.getFileSize())
                .body(new InputStreamResource(in));
    }

    @PostMapping("/{id}/remove")
    @RequirePerm("sys:file:manage")
    public R<Void> remove(@PathVariable Long id) {
        service.remove(id);
        return R.ok(null);
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件（文件上传后端）' % count)
