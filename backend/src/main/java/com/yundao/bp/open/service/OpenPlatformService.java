package com.yundao.bp.open.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.open.dto.ApiCallCmd;
import com.yundao.bp.open.dto.AppCreateCmd;
import com.yundao.bp.open.dto.AppCreatedVO;
import com.yundao.bp.open.entity.OpenApi;
import com.yundao.bp.open.entity.OpenApp;
import com.yundao.bp.open.entity.OpenCallLog;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 开放平台服务。
 *
 * <p><b>三道关卡</b>（顺序不可颠倒）：
 * <ol>
 *   <li>应用有效性：存在 + 启用 + 未过期</li>
 *   <li>访问控制：IP 白名单 + 接口授权范围</li>
 *   <li>签名与防重放：HMAC 签名 + 时间窗口 + nonce</li>
 * </ol>
 * 通过后再做限流，最后落调用日志（无论成功失败都留痕）。
 */
public interface OpenPlatformService {

    /** 创建应用，仅此一次返回明文 secret。 */
    AppCreatedVO createApp(AppCreateCmd cmd, String operator);

    /** 重置密钥（旧密钥立即失效）。 */
    AppCreatedVO resetSecret(Long appId, String operator);

    /** 启用/停用/续期。 */
    OpenApp setStatus(Long appId, String status, String expireDate);

    List<OpenApp> listApps();

    /** 接口清单（可按分组）。 */
    List<OpenApi> listApis(String apiGroup);

    /**
     * 校验一次开放调用（签名 + 白名单 + 授权范围 + 时间窗）。
     *
     * @return 通过返回应用的租户ID；不通过抛 {@code BizException}
     */
    String verify(ApiCallCmd cmd, String clientIp);

    /** 记录调用日志。 */
    void logCall(String appKey, String apiCode, String apiPath, String clientIp,
                 String requestBody, String responseCode, boolean success,
                 String errorMsg, int durationMs);

    PageResult<OpenCallLog> pageCallLogs(long pageNum, long pageSize, String appKey,
                                         String apiCode, Boolean successOnly,
                                         LocalDate dateFrom, LocalDate dateTo);

    /** 用量统计（按应用）。 */
    Map<String, Object> usage(String appKey, LocalDate dateFrom, LocalDate dateTo);
}
