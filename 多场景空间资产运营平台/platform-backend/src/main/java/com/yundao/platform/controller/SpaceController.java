package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.SpaceService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/projects/{projectId}/spaces")
public class SpaceController {

    private final SpaceService service;

    public SpaceController(SpaceService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@PathVariable long projectId) {
        return R.ok(service.list(projectId));
    }

    @PostMapping
    public R<Map<String, Object>> create(@PathVariable long projectId,
                                         @RequestBody SpaceService.SpaceCmd cmd) {
        return R.ok(service.create(projectId, cmd));
    }
}
