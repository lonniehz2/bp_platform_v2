package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.MessageService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/messages")
public class MessageController {

    private final MessageService service;

    public MessageController(MessageService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list() {
        return R.ok(service.list());
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody MessageService.CreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/{id}/read")
    public R<Map<String, Object>> read(@PathVariable long id) {
        return R.ok(service.read(id));
    }

    @PostMapping("/read-all")
    public R<Map<String, Object>> readAll() {
        return R.ok(service.readAll());
    }
}
