package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.UserService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/users")
public class UserController {

    private final UserService service;

    public UserController(UserService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> users() {
        return R.ok(service.users());
    }

    @GetMapping("/roles")
    public R<List<Map<String, Object>>> roles() {
        return R.ok(service.roles());
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody UserService.CreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @GetMapping("/{id}/scopes")
    public R<Map<String, Object>> scopes(@PathVariable long id) {
        return R.ok(service.scopes(id));
    }

    @PostMapping("/{id}/scopes")
    public R<Map<String, Object>> updateScopes(@PathVariable long id,
                                               @RequestBody UserService.ScopeCmd cmd) {
        return R.ok(service.updateScopes(id, cmd));
    }

    @PostMapping("/{id}/update")
    public R<Map<String, Object>> update(@PathVariable long id,
                                         @RequestBody UserService.UpdateCmd cmd) {
        return R.ok(service.update(id, cmd));
    }
}
