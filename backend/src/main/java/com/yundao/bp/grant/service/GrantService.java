package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.dto.GrantApplyCmd;
import com.yundao.bp.grant.dto.GrantTaskVO;
import com.yundao.bp.grant.dto.GrantVO;

/**
 * 授权编排服务。
 */
public interface GrantService {

    /**
     * 申请授权：创建权益 + 创建下发任务（幂等）+ 投递 MQ。
     *
     * <p>返回时任务通常仍为 {@code PENDING}，真正下发是异步的。
     */
    GrantVO apply(GrantApplyCmd cmd);

    GrantVO get(Long id);

    PageResult<GrantVO> page(long pageNum, long pageSize, Long personId, Long spaceId,
                             String grantStatus);

    GrantTaskVO task(Long taskId);

    /** 撤销授权（同时生成 REVOKE 任务）。 */
    GrantVO revoke(Long id, String reason);

    /** 执行下发（供 MQ 消费者/重试任务调用）；幂等。 */
    void dispatch(Long taskId);

    /** 管理权到期自动归还：把 valid_end 已过的生效权益置为 EXPIRED，返回条数。 */
    int expireOverdue();

    /** 授权任务超时判定：下发超过 3 分钟未回调的置为失败，返回条数。 */
    int markTimeout();
}
