package com.yundao.bp.dev.service;

import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.common.api.PageResult;

/** 设备指令（开锁/重启/校时/拉合闸）。 */
public interface DevCommandService {

    DevCommand create(String commandType, String deviceId, String lockId, String meterNo,
                      String reason, String paramsJson, String source);

    PageResult<DevCommand> page(long pageNum, long pageSize, String status, String commandType,
                                String deviceId);

    DevCommand get(Long id);

    DevCommand retry(Long id);

    DevCommand cancel(Long id);

    /** 拉合闸审批（approve=true 通过并下发；false 驳回）。 */
    DevCommand approve(Long id, boolean approve);

    /** 下发（供创建后与超时重试 Job 调用）。 */
    void dispatch(Long id);
}
