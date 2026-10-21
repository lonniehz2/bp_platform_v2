package com.yundao.bp.sys.controller;

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
