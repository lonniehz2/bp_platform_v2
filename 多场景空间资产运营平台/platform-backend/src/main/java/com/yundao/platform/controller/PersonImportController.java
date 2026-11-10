package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.PersonImportService;
import com.yundao.platform.service.SpaceImportService;
import com.yundao.platform.service.RelationImportService;
import com.yundao.platform.service.BindingImportService;
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
    private final RelationImportService relationService;
    private final BindingImportService bindingService;

    public PersonImportController(PersonImportService service, SpaceImportService spaceService,
                                  RelationImportService relationService, BindingImportService bindingService) {
        this.service = service;
        this.spaceService = spaceService;
        this.relationService = relationService;
        this.bindingService = bindingService;
    }

    @PostMapping("/persons")
    public R<Map<String, Object>> persons(@RequestParam("file") MultipartFile file) {
        return R.ok(service.importCsv(file));
    }

    @PostMapping("/device-bindings")
    public R<Map<String, Object>> deviceBindings(@RequestParam("file") MultipartFile file) {
        return R.ok(bindingService.importDeviceBindings(file));
    }

    @PostMapping("/person-assets")
    public R<Map<String, Object>> personAssets(@RequestParam("file") MultipartFile file) {
        return R.ok(relationService.importPersonAssets(file));
    }

    @PostMapping("/spaces")
    public R<Map<String, Object>> spaces(@RequestParam("file") MultipartFile file) {
        return R.ok(spaceService.importCsv(file));
    }
}
