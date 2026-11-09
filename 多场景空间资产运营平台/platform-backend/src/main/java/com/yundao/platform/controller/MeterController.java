package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.MeterService;
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
@RequestMapping("/api/v1/platform/guarantee/meters")
public class MeterController {

    private final MeterService service;

    public MeterController(MeterService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam long projectId) {
        return R.ok(service.meters(projectId));
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody MeterService.MeterCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/{meterId}/update")
    public R<Map<String, Object>> update(@PathVariable long meterId,
                                         @RequestBody MeterService.MeterCmd cmd) {
        return R.ok(service.update(meterId, cmd));
    }

    @PostMapping("/{meterId}/status")
    public R<Map<String, Object>> status(@PathVariable long meterId,
                                         @RequestBody Map<String, String> body) {
        return R.ok(service.setStatus(meterId, body.get("status")));
    }

    @GetMapping("/{meterId}/readings")
    public R<List<Map<String, Object>>> readings(@PathVariable long meterId) {
        return R.ok(service.readings(meterId));
    }

    @PostMapping("/{meterId}/readings")
    public R<Map<String, Object>> read(@PathVariable long meterId,
                                       @RequestBody MeterService.ReadingCmd cmd) {
        return R.ok(service.read(meterId, cmd));
    }

    @GetMapping("/summary")
    public R<List<Map<String, Object>>> summary(@RequestParam long projectId) {
        return R.ok(service.summary(projectId));
    }
}
