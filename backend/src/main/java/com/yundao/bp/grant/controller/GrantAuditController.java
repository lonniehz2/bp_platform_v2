package com.yundao.bp.grant.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.grant.entity.GrantAuditLog;
import com.yundao.bp.grant.service.GrantAuditService;
import com.yundao.bp.iam.security.RequirePerm;
import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 授权审计查询接口（只读，不可改删）。
 */
@RestController
@RequestMapping("/api/v1/grant-audit-logs")
public class GrantAuditController {

    private final GrantAuditService service;

    public GrantAuditController(GrantAuditService service) {
        this.service = service;
    }

    @GetMapping
    @RequirePerm("grant:audit:list")
    public R<PageResult<GrantAuditLog>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String bizType,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.page(pageNum, pageSize, bizType, personId, spaceId, dateFrom, dateTo));
    }

    @GetMapping("/{id}")
    @RequirePerm("grant:audit:list")
    public R<GrantAuditLog> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }
}
