package com.yundao.bp.sys.controller;

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
