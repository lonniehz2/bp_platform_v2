package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.HouseService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/projects/{projectId}/houses")
public class HouseController {

    private final HouseService service;

    public HouseController(HouseService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@PathVariable long projectId) {
        return R.ok(service.list(projectId));
    }
}
