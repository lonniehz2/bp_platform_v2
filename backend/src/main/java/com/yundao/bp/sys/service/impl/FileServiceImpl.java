package com.yundao.bp.sys.service.impl;

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
