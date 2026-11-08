package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.CohabitantService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/guarantee")
public class CohabitantController {

    private final CohabitantService service;

    public CohabitantController(CohabitantService service) {
        this.service = service;
    }

    @GetMapping("/contracts/{contractId}/cohabitants")
    public R<List<Map<String, Object>>> list(@PathVariable long contractId) {
        return R.ok(service.list(contractId));
    }

    @PostMapping("/contracts/{contractId}/cohabitants")
    public R<Map<String, Object>> add(@PathVariable long contractId,
                                      @RequestBody CohabitantService.AddCmd cmd) {
        return R.ok(service.add(contractId, cmd));
    }

    @PostMapping("/contract-cohabitants/{id}/remove")
    public R<Map<String, Object>> remove(@PathVariable long id) {
        return R.ok(service.remove(id));
    }
}
