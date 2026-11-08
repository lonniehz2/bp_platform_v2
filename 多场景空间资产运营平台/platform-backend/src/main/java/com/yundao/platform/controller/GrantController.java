package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.GrantService;
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
@RequestMapping("/api/v1/platform")
public class GrantController {

    private final GrantService service;

    public GrantController(GrantService service) {
        this.service = service;
    }

    @GetMapping("/grants")
    public R<List<Map<String, Object>>> list(@RequestParam long personId,
                                             @RequestParam(required = false) Long projectId) {
        return R.ok(service.list(personId, projectId));
    }

    @PostMapping("/grants")
    public R<Map<String, Object>> create(@RequestBody GrantService.GrantCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/grants/{grantId}/revoke")
    public R<Map<String, Object>> revoke(@PathVariable long grantId,
                                         @RequestBody(required = false) Map<String, String> body) {
        String reason = body == null ? null : body.get("reason");
        return R.ok(service.revoke(grantId, reason));
    }

    @GetMapping("/persons/{personId}/keyring")
    public R<List<Map<String, Object>>> keyring(@PathVariable long personId) {
        return R.ok(service.keyring(personId));
    }
}
