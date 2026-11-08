package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.MigrationExceptionService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/migration/exceptions")
public class MigrationExceptionController {

    private final MigrationExceptionService service;

    public MigrationExceptionController(MigrationExceptionService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam(required = false) String status) {
        return R.ok(service.list(status));
    }

    @PostMapping("/{id}/resolve")
    public R<Map<String, Object>> resolve(@PathVariable long id,
                                          @RequestBody MigrationExceptionService.ResolveCmd cmd) {
        return R.ok(service.resolve(id, cmd));
    }
}
