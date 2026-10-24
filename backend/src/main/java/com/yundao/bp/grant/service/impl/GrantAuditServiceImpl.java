package com.yundao.bp.grant.service.impl;

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
        // scope:ignore 授权审计日志按操作人租户级
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
