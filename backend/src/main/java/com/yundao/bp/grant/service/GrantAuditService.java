package com.yundao.bp.grant.service;

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
