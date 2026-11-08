package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.FileService;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/platform/files")
public class FileController {

    private final FileService service;

    public FileController(FileService service) {
        this.service = service;
    }

    @PostMapping
    public R<Map<String, Object>> upload(@RequestParam String bizType,
                                         @RequestParam long bizId,
                                         @RequestPart MultipartFile file) {
        return R.ok(service.save(bizType, bizId, file));
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam String bizType,
                                             @RequestParam long bizId) {
        return R.ok(service.list(bizType, bizId));
    }

    @GetMapping("/{id}/download")
    public ResponseEntity<Resource> download(@PathVariable long id) {
        Path path = service.path(id);
        Resource resource = new FileSystemResource(path);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"" + service.fileName(id) + "\"")
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .body(resource);
    }
}
