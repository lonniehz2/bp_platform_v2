package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.RelationService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/relations")
public class RelationController {

    private final RelationService service;

    public RelationController(RelationService service) {
        this.service = service;
    }

    @GetMapping("/{type}/{id}")
    public R<Map<String, Object>> relation(@PathVariable String type, @PathVariable long id) {
        if ("CONTRACT".equalsIgnoreCase(type)) return R.ok(service.contract(id));
        if ("PERSON".equalsIgnoreCase(type)) return R.ok(service.person(id));
        if ("HOUSE".equalsIgnoreCase(type)) return R.ok(service.house(id));
        if ("BILL".equalsIgnoreCase(type)) return R.ok(service.bill(id));
        if ("DEVICE".equalsIgnoreCase(type)) return R.ok(service.device(id));
        if ("WORK_ORDER".equalsIgnoreCase(type)) return R.ok(service.workOrder(id));
        if ("APPLICATION".equalsIgnoreCase(type)) return R.ok(service.application(id));
        throw new com.yundao.platform.common.exception.BizException("BP40004", "暂不支持该关联类型", 400);
    }
}
