package com.yundao.bp.dev.service.impl;

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


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按数据范围追加条件（full=true 时组织也过滤）。 */
    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol,
            boolean full) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(personCol, -1L);
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if (!full) {
            return;     // 无组织列时，ORG/ORG_SUB 不额外限制
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }

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
        applyDataScope(qw, DevAccessRecord::getOrgId, DevAccessRecord::getPersonId, true);
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
