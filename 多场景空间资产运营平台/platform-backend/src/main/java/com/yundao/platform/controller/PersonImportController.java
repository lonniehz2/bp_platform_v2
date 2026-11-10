package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.PersonImportService;
import com.yundao.platform.service.SpaceImportService;
import com.yundao.platform.service.RelationImportService;
import com.yundao.platform.service.BindingImportService;
import com.yundao.platform.service.GrantImportService;
import com.yundao.platform.service.UserImportService;
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
    private final GrantImportService grantImportService;
    private final UserImportService userImportService;

    public PersonImportController(PersonImportService service, SpaceImportService spaceService,
                                  RelationImportService relationService, BindingImportService bindingService, GrantImportService grantImportService, UserImportService userImportService) {
        this.service = service;
        this.spaceService = spaceService;
        this.relationService = relationService;
        this.bindingService = bindingService;
        this.grantImportService = grantImportService;
        this.userImportService = userImportService;
    }

    @PostMapping("/persons")
    public R<Map<String, Object>> persons(@RequestParam("file") MultipartFile file) {
        return R.ok(service.importCsv(file));
    }

    @PostMapping("/users")
    public R<Map<String, Object>> users(@RequestParam("file") MultipartFile file) {
        return R.ok(userImportService.importCsv(file));
    }

    @PostMapping("/device-grants")
    public R<Map<String, Object>> deviceGrants(@RequestParam("file") MultipartFile file) {
        return R.ok(grantImportService.importDeviceGrants(file));
    }

    @PostMapping("/grants")
    public R<Map<String, Object>> grants(@RequestParam("file") MultipartFile file) {
        return R.ok(grantImportService.importSpaceGrants(file));
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
