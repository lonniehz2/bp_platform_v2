# -*- coding: utf-8 -*-
"""生成 sys 控制器 + 政策参数键常量 + 接入硬编码常量"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== 参数键常量 ====================
F['sys/constant/ConfigKeys.java'] = '''package com.yundao.bp.sys.constant;

/**
 * 政策参数键（统一管理，避免散落各处的硬编码）。
 *
 * <p>所有键都支持分租户覆盖，实现「不同地区不同政策」。
 */
public final class ConfigKeys {

    private ConfigKeys() {
    }

    // ---------- 公示 ----------
    /** 配租公示最短自然日（默认 7） */
    public static final String PUBLICITY_ALLOC_MIN_DAYS = "biz.publicity.allocation.minDays";
    /** 资格公示最短自然日（默认 5） */
    public static final String PUBLICITY_QUALIFY_MIN_DAYS = "biz.publicity.qualify.minDays";

    // ---------- 信用惩戒 ----------
    /** 严重违规限制申请年限（默认 5） */
    public static final String CREDIT_BAN_YEARS_SEVERE = "biz.credit.banYears.severe";
    /** 一般违规限制申请年限（默认 1） */
    public static final String CREDIT_BAN_YEARS_NORMAL = "biz.credit.banYears.normal";

    // ---------- 腾退 ----------
    /** 腾退过渡期月数（重庆默认 3） */
    public static final String TERMINATION_TRANSITION_MONTHS = "biz.termination.transition.months";
    /** 过渡期租金倍率（重庆默认 1.5） */
    public static final String TERMINATION_TRANSITION_MULTIPLIER =
            "biz.termination.transition.multiplier";
    /** 搬迁期最大月数（成都默认 6） */
    public static final String TERMINATION_RELOCATION_MAX_MONTHS =
            "biz.termination.relocation.maxMonths";

    // ---------- 配租 ----------
    /** 同一租期最大换房次数（成都默认 1） */
    public static final String EXCHANGE_MAX_TIMES = "biz.exchange.maxTimes";
    /** 应换不换加价倍率（重庆默认 1.5） */
    public static final String EXCHANGE_NO_EXCHANGE_MULTIPLIER =
            "biz.exchange.noExchange.multiplier";
    /** 配租房源冻定时长（小时，默认 72） */
    public static final String ALLOCATION_LOCK_HOURS = "biz.allocation.lockHours";

    // ---------- 年审 ----------
    /** 年审逾期天数阈值（默认 0 = 当年内） */
    public static final String REVIEW_OVERDUE_DAYS = "biz.review.overdue.days";

    // ---------- 申诉 ----------
    /** 申诉期限自然日（默认 10） */
    public static final String APPEAL_DEADLINE_DAYS = "biz.appeal.deadlineDays";
}
'''

# ==================== 控制器 ====================
F['sys/controller/SysController.java'] = '''package com.yundao.bp.sys.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.sys.audit.Audit;
import com.yundao.bp.sys.entity.SysAuditLog;
import com.yundao.bp.sys.entity.SysConfig;
import com.yundao.bp.sys.entity.SysDict;
import com.yundao.bp.sys.service.AuditService;
import com.yundao.bp.sys.service.ConfigService;
import com.yundao.bp.sys.service.DictService;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 系统支撑接口：审计日志 / 数据字典 / 系统参数。
 */
@RestController
@RequestMapping("/api/v1/sys")
public class SysController {

    private final AuditService auditService;
    private final DictService dictService;
    private final ConfigService configService;

    public SysController(AuditService auditService, DictService dictService,
                         ConfigService configService) {
        this.auditService = auditService;
        this.dictService = dictService;
        this.configService = configService;
    }

    // ---------- 审计日志 ----------

    /** 审计日志查询（只读，无删改接口）。 */
    @GetMapping("/audit-logs")
    @RequirePerm("sys:audit:list")
    public R<PageResult<SysAuditLog>> pageAudit(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String auditType,
            @RequestParam(required = false) String level,
            @RequestParam(required = false) String operatorName,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(auditService.page(pageNum, pageSize, auditType, level, operatorName,
                dateFrom, dateTo));
    }

    @GetMapping("/audit-logs/{id}")
    @RequirePerm("sys:audit:list")
    public R<SysAuditLog> getAudit(@PathVariable Long id) {
        return R.ok(auditService.get(id));
    }

    // ---------- 数据字典 ----------

    /** 按类型取字典项（前端下拉用）。 */
    @GetMapping("/dicts/{dictType}")
    public R<List<SysDict>> listDict(@PathVariable String dictType) {
        return R.ok(dictService.listByType(dictType));
    }

    /** 按类型取「编码→标签」映射。 */
    @GetMapping("/dicts/{dictType}/map")
    public R<Map<String, String>> mapDict(@PathVariable String dictType) {
        return R.ok(dictService.mapByType(dictType));
    }

    @GetMapping("/dicts")
    public R<List<String>> dictTypes() {
        return R.ok(dictService.types());
    }

    @PostMapping("/dicts")
    @RequirePerm("sys:dict:edit")
    @Audit(type = "DATA", level = "IMPORTANT", action = "新增字典项")
    public R<SysDict> createDict(@RequestBody DictCmd cmd) {
        return R.ok(dictService.create(cmd.dictType(), cmd.dictCode(), cmd.dictLabel(),
                cmd.dictValue(), cmd.sortNo(), cmd.remark()));
    }

    @PostMapping("/dicts/{id}/status")
    @RequirePerm("sys:dict:edit")
    @Audit(type = "DATA", level = "IMPORTANT", action = "修改字典状态")
    public R<SysDict> dictStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(dictService.setStatus(id, cmd.enabled()));
    }

    // ---------- 系统参数 ----------

    @GetMapping("/configs")
    @RequirePerm("sys:config:list")
    public R<List<SysConfig>> listConfig(@RequestParam(required = false) String group) {
        return group == null || group.isBlank()
                ? R.ok(configService.listAll()) : R.ok(configService.listByGroup(group));
    }

    /** 读取单个参数（含类型化取值）。 */
    @GetMapping("/configs/{key}")
    public R<String> getConfig(@PathVariable String key) {
        return R.ok(configService.getString(key, null));
    }

    /**
     * 设置参数（政策调整入口）。
     *
     * <p>⚠️ 影响后续业务计算，记 CRITICAL 审计。
     */
    @PostMapping("/configs")
    @RequirePerm("sys:config:edit")
    @Audit(type = "DATA", level = "CRITICAL", action = "修改系统参数")
    public R<SysConfig> setConfig(@RequestBody ConfigCmd cmd) {
        return R.ok(configService.set(cmd.key(), cmd.value(), cmd.description()));
    }

    public record DictCmd(String dictType, String dictCode, String dictLabel, String dictValue,
                          Integer sortNo, String remark) {
    }

    public record StatusCmd(boolean enabled) {
    }

    public record ConfigCmd(String key, String value, String description) {
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
