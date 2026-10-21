package com.yundao.bp.sys.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.sys.entity.SysAuditLog;
import java.time.LocalDate;

/**
 * 审计日志服务（只追加，不提供修改/删除）。
 */
public interface AuditService {

    /** 写审计（失败不抛出，调用方自行决定是否忽略）。 */
    void record(String auditType, String auditLevel, String bizType, Long bizId,
                Long operatorId, String operatorName,
                String targetType, String targetId, String action,
                String beforeJson, String afterJson, String reason, String clientIp);

    PageResult<SysAuditLog> page(long pageNum, long pageSize, String auditType, String level,
                                 String operatorName, LocalDate dateFrom, LocalDate dateTo);

    SysAuditLog get(Long id);
}
