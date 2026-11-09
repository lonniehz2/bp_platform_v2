package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.ProjectService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/projects")
public class ProjectController {

    private final ProjectService service;

    public ProjectController(ProjectService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list() {
        return R.ok(service.list());
    }

    @PostMapping("/{projectId}/update")
    public R<Map<String, Object>> update(@org.springframework.web.bind.annotation.PathVariable long projectId,
                                         @RequestBody ProjectService.ProjectCmd cmd) {
        return R.ok(service.update(projectId, cmd));
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody ProjectService.ProjectCmd cmd) {
        return R.ok(service.create(cmd));
    }
}
