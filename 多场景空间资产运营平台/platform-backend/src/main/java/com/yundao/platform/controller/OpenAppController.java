package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.OpenAppService;
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
@RequestMapping("/api/v1/platform/open-apps")
public class OpenAppController {

    private final OpenAppService service;

    public OpenAppController(OpenAppService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list() {
        return R.ok(service.list());
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody OpenAppService.CreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/{id}/toggle")
    public R<Map<String, Object>> toggle(@PathVariable long id, @RequestParam boolean enabled) {
        return R.ok(service.toggle(id, enabled));
    }
}
