package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class FileService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final Path root;

    public FileService(JdbcTemplate jdbc, IdGenerator idGen,
                       @Value("${bp.file.root:uploads}") String root) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.root = Paths.get(root).toAbsolutePath().normalize();
    }

    public Map<String, Object> save(String bizType, long bizId, MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw BizException.param("文件不能为空");
        }
        if (file.getSize() > 20L * 1024 * 1024) {
            throw BizException.param("文件不能超过 20MB");
        }
        String original = file.getOriginalFilename() == null ? "file" : file.getOriginalFilename();
        String safeName = original.replaceAll("[\\\\/:*?\"<>|]", "_");
        String stored = UUID.randomUUID().toString().replace("-", "");
        Path dir = root.resolve(TenantContext.require()).resolve(stored.substring(0, 2));
        Path target = dir.resolve(stored + "_" + safeName);
        try {
            Files.createDirectories(dir);
            file.transferTo(target.toFile());
        } catch (IOException e) {
            throw new BizException("BP50010", "文件保存失败", 500);
        }
        long id = idGen.nextId();
        String uploader = UserContext.get() == null ? null : UserContext.get().displayName();
        jdbc.update("insert into bp_file(id,tenant_id,biz_type,biz_id,file_name,content_type,file_size,"
                        + "storage_path,uploader,is_deleted) values(?,?,?,?,?,?,?,?,?,0)",
                id, TenantContext.require(), bizType, bizId, safeName, file.getContentType(),
                file.getSize(), target.toString(), uploader);
        return Map.of("id", id, "fileName", safeName, "fileSize", file.getSize());
    }

    public List<Map<String, Object>> list(String bizType, long bizId) {
        return jdbc.queryForList(
                "select id, biz_type bizType, biz_id bizId, file_name fileName, content_type contentType, "
                        + "file_size fileSize, uploader, create_time createTime from bp_file "
                        + "where tenant_id=? and biz_type=? and biz_id=? and is_deleted=0 order by id desc",
                TenantContext.require(), bizType, bizId);
    }

    public Path path(long id) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select storage_path storagePath from bp_file where id=? and tenant_id=? and is_deleted=0",
                id, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.notFound("附件不存在");
        }
        Path path = Paths.get(String.valueOf(rows.get(0).get("storagePath"))).normalize();
        if (!path.startsWith(root) || !Files.exists(path)) {
            throw BizException.notFound("附件文件不存在");
        }
        return path;
    }

    public String fileName(long id) {
        return jdbc.queryForObject("select file_name from bp_file where id=? and tenant_id=?",
                String.class, id, TenantContext.require());
    }
}
