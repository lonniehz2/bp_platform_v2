# -*- coding: utf-8 -*-
"""生成通行记录/授权审计实现 + 接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['dev/service/impl/AccessRecordServiceImpl.java'] = '''package com.yundao.bp.dev.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.dto.AccessReportCmd;
import com.yundao.bp.dev.dto.AccessVO;
import com.yundao.bp.dev.dto.IdleStatVO;
import com.yundao.bp.dev.dto.TraceVO;
import com.yundao.bp.dev.entity.DevAccessRecord;
import com.yundao.bp.dev.mapper.DevAccessRecordMapper;
import com.yundao.bp.dev.service.AccessRecordService;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 通行记录实现。
 */
@Service
public class AccessRecordServiceImpl implements AccessRecordService {

    private static final Logger log = LoggerFactory.getLogger(AccessRecordServiceImpl.class);

    /** 可信开门方式码（人脸/指纹/密码/卡片等）；试验性质码视为不可信 */
    private static final java.util.Set<String> TRUSTED_TYPES = java.util.Set.of(
            "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008");

    private final DevAccessRecordMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public AccessRecordServiceImpl(DevAccessRecordMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean report(AccessReportCmd cmd) {
        // 幂等：event_id 已存在则丢弃
        Long dup = mapper.selectCount(new LambdaQueryWrapper<DevAccessRecord>()
                .eq(DevAccessRecord::getEventId, cmd.eventId()));
        if (dup != null && dup > 0) {
            return false;
        }
        DevAccessRecord e = new DevAccessRecord();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setEventId(cmd.eventId());
        e.setLockId(cmd.lockId());
        e.setDeviceId(cmd.deviceId());
        e.setDeviceMac(cmd.deviceMac());
        e.setSpaceId(cmd.spaceId());
        e.setHouseId(cmd.houseId());
        e.setOrgId(cmd.orgId());
        e.setOpenType(cmd.openType());
        e.setOpenTypeName(openTypeName(cmd.openType()));
        e.setIsTrusted(TRUSTED_TYPES.contains(cmd.openType()) ? 1 : 0);
        e.setPersonId(cmd.personId());
        e.setTargetUserMobile(cmd.targetUserMobile());
        e.setOpenTime(cmd.openTime());
        e.setSource(cmd.source() == null ? "CALLBACK" : cmd.source());
        boolean abnormal = Boolean.TRUE.equals(cmd.abnormal())
                || !TRUSTED_TYPES.contains(cmd.openType());
        e.setIsAbnormal(abnormal ? 1 : 0);
        e.setAbnormalType(abnormal
                ? (cmd.abnormalType() == null ? "OTHER" : cmd.abnormalType()) : null);
        e.setCreateTime(LocalDateTime.now());
        mapper.insert(e);
        if (abnormal) {
            log.warn("异常开门：房源 {} 人 {} 方式 {}（{}）", cmd.houseId(), cmd.personId(),
                    cmd.openType(), e.getAbnormalType());
        }
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int reportBatch(List<AccessReportCmd> cmds) {
        int n = 0;
        for (AccessReportCmd c : cmds) {
            if (report(c)) {
                n++;
            }
        }
        return n;
    }

    @Override
    public PageResult<AccessVO> page(long pageNum, long pageSize, Long personId, Long houseId,
                                     LocalDate dateFrom, LocalDate dateTo,
                                     Boolean abnormalOnly) {
        LambdaQueryWrapper<DevAccessRecord> qw = new LambdaQueryWrapper<DevAccessRecord>()
                .eq(personId != null, DevAccessRecord::getPersonId, personId)
                .eq(houseId != null, DevAccessRecord::getHouseId, houseId)
                .eq(Boolean.TRUE.equals(abnormalOnly), DevAccessRecord::getIsAbnormal, 1)
                .orderByDesc(DevAccessRecord::getOpenTime)
                .orderByDesc(DevAccessRecord::getId);
        if (dateFrom != null) {
            qw.ge(DevAccessRecord::getOpenTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(DevAccessRecord::getOpenTime, dateTo.plusDays(1).atStartOfDay());
        }
        IPage<DevAccessRecord> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<AccessVO> rows = page.getRecords().stream().map(AccessVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public TraceVO traceByPerson(Long personId, LocalDate dateFrom, LocalDate dateTo) {
        List<DevAccessRecord> list = load(new LambdaQueryWrapper<DevAccessRecord>()
                .eq(DevAccessRecord::getPersonId, personId), dateFrom, dateTo);
        return buildTrace("PERSON", personId, dateFrom, dateTo, list);
    }

    @Override
    public TraceVO traceByHouse(Long houseId, LocalDate dateFrom, LocalDate dateTo) {
        List<DevAccessRecord> list = load(new LambdaQueryWrapper<DevAccessRecord>()
                .eq(DevAccessRecord::getHouseId, houseId), dateFrom, dateTo);
        return buildTrace("HOUSE", houseId, dateFrom, dateTo, list);
    }

    @Override
    public List<IdleStatVO> detectIdle(Long orgId, int idleDays) {
        int threshold = idleDays <= 0 ? 30 : idleDays;
        List<DevAccessRecord> all = mapper.selectList(new LambdaQueryWrapper<DevAccessRecord>()
                .eq(orgId != null, DevAccessRecord::getOrgId, orgId)
                .isNotNull(DevAccessRecord::getHouseId)
                .orderByDesc(DevAccessRecord::getOpenTime));
        // 每房源取最近一次开门
        Map<Long, DevAccessRecord> lastByHouse = new LinkedHashMap<>();
        for (DevAccessRecord r : all) {
            lastByHouse.putIfAbsent(r.getHouseId(), r);
        }
        LocalDateTime now = LocalDateTime.now();
        List<IdleStatVO> out = new ArrayList<>();
        for (Map.Entry<Long, DevAccessRecord> en : lastByHouse.entrySet()) {
            DevAccessRecord r = en.getValue();
            long days = Duration.between(r.getOpenTime(), now).toDays();
            out.add(new IdleStatVO(en.getKey(), r.getSpaceId(), r.getOrgId(),
                    r.getOpenTime(), days, days >= threshold,
                    days >= threshold
                            ? "连续 " + days + " 天无开门记录，疑似空置（阈值 " + threshold + " 天）"
                            : "正常"));
        }
        out.sort((a, b) -> Long.compare(b.idleDays(), a.idleDays()));
        return out;
    }

    @Override
    public Map<String, Object> untrustedRatio(Long orgId, LocalDate dateFrom, LocalDate dateTo) {
        List<DevAccessRecord> list = load(new LambdaQueryWrapper<DevAccessRecord>()
                .eq(orgId != null, DevAccessRecord::getOrgId, orgId), dateFrom, dateTo);
        long total = list.size();
        long untrusted = list.stream()
                .filter(r -> r.getIsTrusted() == null || r.getIsTrusted() == 0).count();
        Map<String, Object> m = new HashMap<>();
        m.put("total", total);
        m.put("untrusted", untrusted);
        m.put("untrustedRatio", total == 0 ? 0.0
                : Math.round(untrusted * 10000.0 / total) / 100.0);
        m.put("threshold", 20.0);
        m.put("pass", total == 0 || (untrusted * 100.0 / total) <= 20.0);
        return m;
    }

    // ==================== 内部 ====================

    private List<DevAccessRecord> load(LambdaQueryWrapper<DevAccessRecord> qw,
                                       LocalDate dateFrom, LocalDate dateTo) {
        if (dateFrom != null) {
            qw.ge(DevAccessRecord::getOpenTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(DevAccessRecord::getOpenTime, dateTo.plusDays(1).atStartOfDay());
        }
        qw.orderByAsc(DevAccessRecord::getOpenTime);
        return mapper.selectList(qw);
    }

    private static TraceVO buildTrace(String scope, Long targetId, LocalDate from,
                                      LocalDate to, List<DevAccessRecord> list) {
        List<AccessVO> timeline = list.stream().map(AccessVO::from).toList();
        int abnormal = (int) list.stream()
                .filter(r -> r.getIsAbnormal() != null && r.getIsAbnormal() == 1).count();
        String summary;
        if (list.isEmpty()) {
            summary = "区间内无开门记录";
        } else {
            LocalDateTime first = list.get(0).getOpenTime();
            LocalDateTime last = list.get(list.size() - 1).getOpenTime();
            summary = "共 " + list.size() + " 次开门，首次 " + first + "，最近 " + last
                    + (abnormal > 0 ? "，其中异常 " + abnormal + " 次" : "");
        }
        return new TraceVO(scope, targetId, from, to, list.size(), abnormal, summary, timeline);
    }

    private static String openTypeName(String code) {
        if (code == null) {
            return null;
        }
        return switch (code) {
            case "1001" -> "人脸";
            case "1002" -> "指纹";
            case "1003" -> "密码";
            case "1004" -> "卡片";
            case "1005" -> "钥匙";
            case "1006" -> "App远程";
            case "1007" -> "身份证";
            case "1008" -> "二维码";
            case "1901" -> "临时密码";
            default -> "方式" + code;
        };
    }
}
'''

# ==================== 授权审计服务 ====================
F['grant/service/GrantAuditService.java'] = '''package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.entity.GrantAuditLog;
import java.time.LocalDate;

/**
 * 授权操作审计（★ 级要求：不可篡改可追溯）。
 *
 * <p>只提供「写」与「查」，<b>不提供改与删</b>。
 */
public interface GrantAuditService {

    /** 记一条授权审计（失败不抛出，避免影响授权主流程）。 */
    void record(String bizType, Long bizId, Long personId, Long spaceId,
                Long operatorId, String operatorName, String reason,
                String beforeJson, String afterJson, String result);

    PageResult<GrantAuditLog> page(long pageNum, long pageSize, String bizType, Long personId,
                                   Long spaceId, LocalDate dateFrom, LocalDate dateTo);

    GrantAuditLog get(Long id);
}
'''

F['grant/service/impl/GrantAuditServiceImpl.java'] = '''package com.yundao.bp.grant.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.grant.entity.GrantAuditLog;
import com.yundao.bp.grant.mapper.GrantAuditLogMapper;
import com.yundao.bp.grant.service.GrantAuditService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/**
 * 授权审计实现。
 */
@Service
public class GrantAuditServiceImpl implements GrantAuditService {

    private static final Logger log = LoggerFactory.getLogger(GrantAuditServiceImpl.class);
    private static final ObjectMapper JSON = new ObjectMapper();

    private final GrantAuditLogMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public GrantAuditServiceImpl(GrantAuditLogMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public void record(String bizType, Long bizId, Long personId, Long spaceId,
                       Long operatorId, String operatorName, String reason,
                       String beforeJson, String afterJson, String result) {
        try {
            GrantAuditLog e = new GrantAuditLog();
            e.setId(idGen.nextId());
            e.setTenantId(TenantContext.tenantId());
            e.setBizType(bizType);
            e.setBizId(bizId);
            e.setPersonId(personId);
            e.setSpaceId(spaceId);
            e.setOperatorId(operatorId);
            e.setOperatorName(operatorName);
            e.setReason(reason);
            // JSON 列必须合法：统一包成 {"text": "..."}
            e.setBeforeJson(wrap(beforeJson));
            e.setAfterJson(wrap(afterJson));
            e.setResult(result == null ? "SUCCESS" : result);
            e.setCreateTime(LocalDateTime.now());
            mapper.insert(e);
        } catch (Exception ex) {
            log.warn("写授权审计失败（不影响授权主流程）：{}", ex.getMessage());
        }
    }

    @Override
    public PageResult<GrantAuditLog> page(long pageNum, long pageSize, String bizType,
                                          Long personId, Long spaceId, LocalDate dateFrom,
                                          LocalDate dateTo) {
        LambdaQueryWrapper<GrantAuditLog> qw = new LambdaQueryWrapper<GrantAuditLog>()
                .eq(bizType != null && !bizType.isBlank(), GrantAuditLog::getBizType, bizType)
                .eq(personId != null, GrantAuditLog::getPersonId, personId)
                .eq(spaceId != null, GrantAuditLog::getSpaceId, spaceId)
                .orderByDesc(GrantAuditLog::getId);
        if (dateFrom != null) {
            qw.ge(GrantAuditLog::getCreateTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(GrantAuditLog::getCreateTime, dateTo.plusDays(1).atStartOfDay());
        }
        IPage<GrantAuditLog> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<GrantAuditLog> rows = page.getRecords();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public GrantAuditLog get(Long id) {
        GrantAuditLog e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("授权审计");
        }
        return e;
    }

    private static String wrap(String s) {
        if (s == null) {
            return null;
        }
        try {
            LinkedHashMap<String, Object> m = new LinkedHashMap<>();
            m.put("text", s.length() > 1800 ? s.substring(0, 1800) + "...(截断)" : s);
            return JSON.writeValueAsString(m);
        } catch (Exception e) {
            return null;
        }
    }
}
'''

# ==================== 控制器 ====================
F['dev/controller/AccessRecordController.java'] = '''package com.yundao.bp.dev.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.dev.dto.AccessReportCmd;
import com.yundao.bp.dev.dto.AccessVO;
import com.yundao.bp.dev.dto.IdleStatVO;
import com.yundao.bp.dev.dto.TraceVO;
import com.yundao.bp.dev.service.AccessRecordService;
import com.yundao.bp.iam.security.RequirePerm;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 通行记录接口（BC-04）。
 *
 * <p>数据源：IoT 开门回调写入 / 定时拉取补齐。支撑行为轨迹、空置判定、异常开门告警。
 */
@RestController
@RequestMapping("/api/v1/access-records")
public class AccessRecordController {

    private final AccessRecordService service;

    public AccessRecordController(AccessRecordService service) {
        this.service = service;
    }

    /** 上报一条（供 IoT 回调或补偿）。 */
    @PostMapping
    @RequirePerm("dev:access:report")
    public R<Boolean> report(@Valid @RequestBody AccessReportCmd cmd) {
        return R.ok(service.report(cmd));
    }

    /** 批量上报。 */
    @PostMapping("/batch")
    @RequirePerm("dev:access:report")
    public R<Integer> reportBatch(@Valid @RequestBody List<AccessReportCmd> cmds) {
        return R.ok(service.reportBatch(cmds));
    }

    @GetMapping
    public R<PageResult<AccessVO>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo,
            @RequestParam(required = false) Boolean abnormalOnly) {
        return R.ok(service.page(pageNum, pageSize, personId, houseId, dateFrom, dateTo,
                abnormalOnly));
    }

    /** ⭐ 人员行为轨迹。 */
    @GetMapping("/trace/person/{personId}")
    public R<TraceVO> tracePerson(
            @org.springframework.web.bind.annotation.PathVariable Long personId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.traceByPerson(personId, dateFrom, dateTo));
    }

    /** ⭐ 房源行为轨迹。 */
    @GetMapping("/trace/house/{houseId}")
    public R<TraceVO> traceHouse(
            @org.springframework.web.bind.annotation.PathVariable Long houseId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.traceByHouse(houseId, dateFrom, dateTo));
    }

    /** ⭐ 空置判定。 */
    @GetMapping("/idle")
    public R<List<IdleStatVO>> idle(@RequestParam(required = false) Long orgId,
                                    @RequestParam(defaultValue = "30") int idleDays) {
        return R.ok(service.detectIdle(orgId, idleDays));
    }

    /** 不可信开门占比（考核指标）。 */
    @GetMapping("/untrusted-ratio")
    public R<Map<String, Object>> untrustedRatio(
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.untrustedRatio(orgId, dateFrom, dateTo));
    }
}
'''

F['grant/controller/GrantAuditController.java'] = '''package com.yundao.bp.grant.controller;

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
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
