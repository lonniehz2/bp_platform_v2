package com.yundao.bp.sys.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.entity.SysAuditLog;
import com.yundao.bp.sys.mapper.SysAuditLogMapper;
import com.yundao.bp.sys.service.AuditService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/**
 * 审计日志实现。
 *
 * <p>写审计用 {@code REQUIRES_NEW}：即使主业务回滚，审计也要留痕
 * （例如操作失败本身也需要记录）。
 */
@Service
public class AuditServiceImpl implements AuditService {

    private final SysAuditLogMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public AuditServiceImpl(SysAuditLogMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public void record(String auditType, String auditLevel, String bizType, Long bizId,
                       Long operatorId, String operatorName,
                       String targetType, String targetId, String action,
                       String beforeJson, String afterJson, String reason, String clientIp) {
        LocalDateTime now = LocalDateTime.now();
        SysAuditLog e = new SysAuditLog();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setAuditType(auditType == null ? "OTHER" : auditType);
        e.setAuditLevel(auditLevel == null ? "NORMAL" : auditLevel);
        e.setBizType(bizType);
        e.setBizId(bizId);
        e.setOperatorId(operatorId);
        e.setOperatorName(operatorName);
        e.setTargetType(targetType);
        e.setTargetId(targetId);
        e.setAction(action);
        e.setBeforeJson(beforeJson);
        e.setAfterJson(afterJson);
        e.setReason(reason);
        e.setClientIp(clientIp);
        e.setAuditTime(now);
        e.setCreateTime(now);
        mapper.insert(e);
    }

    @Override
    public PageResult<SysAuditLog> page(long pageNum, long pageSize, String auditType,
                                        String level, String operatorName, LocalDate dateFrom,
                                        LocalDate dateTo) {
        LambdaQueryWrapper<SysAuditLog> qw = new LambdaQueryWrapper<SysAuditLog>()
                .eq(auditType != null && !auditType.isBlank(),
                        SysAuditLog::getAuditType, auditType)
                .eq(level != null && !level.isBlank(), SysAuditLog::getAuditLevel, level)
                .like(operatorName != null && !operatorName.isBlank(),
                        SysAuditLog::getOperatorName, operatorName)
                .orderByDesc(SysAuditLog::getId);
        if (dateFrom != null) {
            qw.ge(SysAuditLog::getAuditTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(SysAuditLog::getAuditTime, dateTo.plusDays(1).atStartOfDay());
        }
        IPage<SysAuditLog> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<SysAuditLog> rows = page.getRecords();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public SysAuditLog get(Long id) {
        SysAuditLog e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("审计日志");
        }
        return e;
    }
}
