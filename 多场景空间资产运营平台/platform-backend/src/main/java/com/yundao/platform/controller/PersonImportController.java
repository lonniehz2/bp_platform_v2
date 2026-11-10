package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.PersonImportService;
import com.yundao.platform.service.SpaceImportService;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/platform/imports")
public class PersonImportController {

    private final PersonImportService service;
    private final SpaceImportService spaceService;

    public PersonImportController(PersonImportService service, SpaceImportService spaceService) {
        this.service = service;
        this.spaceService = spaceService;
    }

    @PostMapping("/persons")
    public R<Map<String, Object>> persons(@RequestParam("file") MultipartFile file) {
        return R.ok(service.importCsv(file));
    }

    @PostMapping("/spaces")
    public R<Map<String, Object>> spaces(@RequestParam("file") MultipartFile file) {
        return R.ok(spaceService.importCsv(file));
    }
}
