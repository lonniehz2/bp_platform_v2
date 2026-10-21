package com.yundao.bp.open.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.open.dto.ApiCallCmd;
import com.yundao.bp.open.dto.AppCreateCmd;
import com.yundao.bp.open.dto.AppCreatedVO;
import com.yundao.bp.open.entity.OpenApi;
import com.yundao.bp.open.entity.OpenApp;
import com.yundao.bp.open.entity.OpenCallLog;
import com.yundao.bp.open.mapper.OpenApiMapper;
import com.yundao.bp.open.mapper.OpenAppMapper;
import com.yundao.bp.open.mapper.OpenCallLogMapper;
import com.yundao.bp.open.security.OpenSigner;
import com.yundao.bp.open.security.SecretCipher;
import com.yundao.bp.open.service.OpenPlatformService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 开放平台实现。
 */
@Service
public class OpenPlatformServiceImpl implements OpenPlatformService {

    private static final Logger log = LoggerFactory.getLogger(OpenPlatformServiceImpl.class);

    private final OpenAppMapper appMapper;
    private final OpenApiMapper apiMapper;
    private final OpenCallLogMapper callLogMapper;
    private final OpenSigner signer;
    private final SecretCipher cipher;
    private final SnowflakeIdGenerator idGen;

    public OpenPlatformServiceImpl(OpenAppMapper appMapper, OpenApiMapper apiMapper,
                                   OpenCallLogMapper callLogMapper, OpenSigner signer,
                                   SecretCipher cipher, SnowflakeIdGenerator idGen) {
        this.appMapper = appMapper;
        this.apiMapper = apiMapper;
        this.callLogMapper = callLogMapper;
        this.signer = signer;
        this.cipher = cipher;
        this.idGen = idGen;
    }

    // ==================== 应用管理 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppCreatedVO createApp(AppCreateCmd cmd, String operator) {
        String secret = signer.newSecret();
        LocalDateTime now = LocalDateTime.now();
        OpenApp a = new OpenApp();
        a.setId(idGen.nextId());
        a.setTenantId(TenantContext.tenantId());
        a.setAppKey(signer.newAppKey());
        // 加密存储（签名校验需还原明文；不能存哈希）
        a.setAppSecret(cipher.encrypt(secret));
        a.setAppName(cmd.appName());
        a.setAppType(cmd.appType() == null ? "THIRD_PARTY" : cmd.appType());
        a.setOwnerOrg(cmd.ownerOrg());
        a.setContactName(cmd.contactName());
        a.setContactPhone(cmd.contactPhone());
        a.setIpWhitelist(cmd.ipWhitelist());
        a.setQpsLimit(cmd.qpsLimit() == null ? 20 : cmd.qpsLimit());
        a.setDailyQuota(cmd.dailyQuota());
        a.setScopeCodes(cmd.scopeCodes() == null ? "*" : cmd.scopeCodes());
        if (cmd.expireDate() != null && !cmd.expireDate().isBlank()) {
            a.setExpireDate(LocalDate.parse(cmd.expireDate()));
        }
        a.setAppStatus("ENABLED");
        a.setIsDeleted(0);
        a.setCreateBy(operator);
        a.setCreateTime(now);
        a.setUpdateTime(now);
        appMapper.insert(a);
        log.info("开放平台应用已创建：{}（{}），范围 {}", a.getAppKey(), a.getAppName(),
                a.getScopeCodes());
        return AppCreatedVO.from(a, secret);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppCreatedVO resetSecret(Long appId, String operator) {
        OpenApp a = requireApp(appId);
        String secret = signer.newSecret();
        a.setAppSecret(cipher.encrypt(secret));
        a.setUpdateBy(operator);
        a.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(a);
        log.warn("开放平台应用密钥已重置：{}（旧密钥立即失效）", a.getAppKey());
        return AppCreatedVO.from(a, secret);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OpenApp setStatus(Long appId, String status, String expireDate) {
        OpenApp a = requireApp(appId);
        if (status != null && !status.isBlank()) {
            if (!List.of("ENABLED", "DISABLED", "EXPIRED").contains(status)) {
                throw BizException.paramInvalid("非法应用状态：" + status);
            }
            a.setAppStatus(status);
        }
        if (expireDate != null && !expireDate.isBlank()) {
            a.setExpireDate(LocalDate.parse(expireDate));
        }
        a.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(a);
        return a;
    }

    @Override
    public List<OpenApp> listApps() {
        return appMapper.selectList(new LambdaQueryWrapper<OpenApp>()
                .orderByDesc(OpenApp::getId));
    }

    @Override
    public List<OpenApi> listApis(String apiGroup) {
        return apiMapper.selectList(new LambdaQueryWrapper<OpenApi>()
                .eq(apiGroup != null && !apiGroup.isBlank(), OpenApi::getApiGroup, apiGroup)
                .eq(OpenApi::getApiStatus, "ENABLED")
                .orderByAsc(OpenApi::getApiCode));
    }

    // ==================== 调用校验 ====================

    @Override
    public String verify(ApiCallCmd cmd, String clientIp) {
        // 关卡1：应用有效性
        OpenApp app = appMapper.selectOne(new LambdaQueryWrapper<OpenApp>()
                .eq(OpenApp::getAppKey, cmd.appKey())
                .last("LIMIT 1"));
        if (app == null) {
            throw fail(ErrorCode.UNAUTHORIZED, "AppKey 不存在");
        }
        if (!"ENABLED".equals(app.getAppStatus())) {
            throw fail(ErrorCode.FORBIDDEN, "应用已停用或已过期：" + app.getAppStatus());
        }
        if (app.getExpireDate() != null && app.getExpireDate().isBefore(LocalDate.now())) {
            throw fail(ErrorCode.FORBIDDEN, "应用已过有效期：" + app.getExpireDate());
        }

        // 关卡2：访问控制
        if (!signer.ipAllowed(app.getIpWhitelist(), clientIp)) {
            throw fail(ErrorCode.FORBIDDEN, "IP 不在白名单：" + clientIp);
        }
        if (!scopeAllowed(app.getScopeCodes(), cmd.apiCode())) {
            throw fail(ErrorCode.FORBIDDEN,
                    "应用未获授权访问接口：" + cmd.apiCode());
        }

        // 关卡3：签名与防重放
        long ts;
        try {
            ts = Long.parseLong(cmd.timestamp().trim());
        } catch (Exception e) {
            throw fail(ErrorCode.PARAM_INVALID, "timestamp 必须是毫秒数字");
        }
        if (!signer.freshTimestamp(ts, System.currentTimeMillis())) {
            throw fail(ErrorCode.UNAUTHORIZED,
                    "请求已过期（时间偏差超过 " + (OpenSigner.MAX_SKEW_MS / 1000) + " 秒）");
        }
        String payload = signer.buildPayload("POST", "/open/" + cmd.apiCode(),
                cmd.timestamp(), cmd.nonce(), cmd.body());
        String plainSecret = cipher.decrypt(app.getAppSecret());
        String expect = signer.sign(plainSecret, payload);
        if (!signer.verify(expect, cmd.sign())) {
            throw fail(ErrorCode.UNAUTHORIZED, "签名校验失败");
        }

        log.debug("开放调用通过：{} → {}（租户 {}）", app.getAppKey(), cmd.apiCode(),
                app.getTenantId());
        return app.getTenantId();
    }

    @Override
    public void logCall(String appKey, String apiCode, String apiPath, String clientIp,
                        String requestBody, String responseCode, boolean success,
                        String errorMsg, int durationMs) {
        try {
            OpenCallLog l = new OpenCallLog();
            l.setId(idGen.nextId());
            l.setAppKey(appKey);
            l.setApiCode(apiCode);
            l.setApiPath(apiPath);
            l.setRequestId("REQ" + l.getId());
            l.setClientIp(clientIp);
            l.setRequestBody(mask(requestBody));
            l.setResponseCode(responseCode);
            l.setSuccessFlag(success ? 1 : 0);
            l.setErrorMsg(errorMsg);
            l.setDurationMs(durationMs);
            l.setCallTime(LocalDateTime.now());
            l.setCreateTime(LocalDateTime.now());
            callLogMapper.insert(l);
        } catch (Exception ex) {
            log.warn("写开放调用日志失败（不影响主流程）：{}", ex.getMessage());
        }
    }

    @Override
    public PageResult<OpenCallLog> pageCallLogs(long pageNum, long pageSize, String appKey,
                                                String apiCode, Boolean successOnly,
                                                LocalDate dateFrom, LocalDate dateTo) {
        LambdaQueryWrapper<OpenCallLog> qw = new LambdaQueryWrapper<OpenCallLog>()
                .eq(appKey != null && !appKey.isBlank(), OpenCallLog::getAppKey, appKey)
                .eq(apiCode != null && !apiCode.isBlank(), OpenCallLog::getApiCode, apiCode)
                .eq(Boolean.TRUE.equals(successOnly), OpenCallLog::getSuccessFlag, 1)
                .eq(Boolean.FALSE.equals(successOnly), OpenCallLog::getSuccessFlag, 0)
                .orderByDesc(OpenCallLog::getId);
        if (dateFrom != null) {
            qw.ge(OpenCallLog::getCallTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(OpenCallLog::getCallTime, dateTo.plusDays(1).atStartOfDay());
        }
        IPage<OpenCallLog> page = callLogMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    public Map<String, Object> usage(String appKey, LocalDate dateFrom, LocalDate dateTo) {
        LambdaQueryWrapper<OpenCallLog> qw = new LambdaQueryWrapper<OpenCallLog>()
                .eq(appKey != null && !appKey.isBlank(), OpenCallLog::getAppKey, appKey);
        if (dateFrom != null) {
            qw.ge(OpenCallLog::getCallTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(OpenCallLog::getCallTime, dateTo.plusDays(1).atStartOfDay());
        }
        List<OpenCallLog> list = callLogMapper.selectList(qw);
        long ok = list.stream().filter(l -> l.getSuccessFlag() != null
                && l.getSuccessFlag() == 1).count();
        int totalMs = list.stream()
                .mapToInt(l -> l.getDurationMs() == null ? 0 : l.getDurationMs()).sum();
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("appKey", appKey);
        m.put("total", list.size());
        m.put("success", ok);
        m.put("failed", list.size() - ok);
        m.put("successRate", list.isEmpty() ? 0.0
                : Math.round(ok * 10000.0 / list.size()) / 100.0);
        m.put("avgDurationMs", list.isEmpty() ? 0 : totalMs / list.size());
        return m;
    }

    // ==================== 内部 ====================

    private OpenApp requireApp(Long appId) {
        OpenApp a = appMapper.selectById(appId);
        if (a == null) {
            throw BizException.notFound("开放应用");
        }
        return a;
    }

    /** 接口范围校验：* 表示全部；否则逗号分隔精确匹配。 */
    private static boolean scopeAllowed(String scopeCodes, String apiCode) {
        if (scopeCodes == null || scopeCodes.isBlank()) {
            return false;
        }
        String s = scopeCodes.trim();
        if ("*".equals(s)) {
            return true;
        }
        for (String c : s.split(",")) {
            if (c.trim().equals(apiCode)) {
                return true;
            }
        }
        return false;
    }

    /** 请求体脱敏：截断 + 掩掉疑似手机号/证件号。 */
    private static String mask(String body) {
        if (body == null) {
            return null;
        }
        String s = body.length() > 1800 ? body.substring(0, 1800) + "...(截断)" : body;
        s = s.replaceAll("1[3-9]\\d{9}", "1**********");
        s = s.replaceAll("\\d{17}[\\dXx]", "******************");
        return s;
    }

    private static BizException fail(ErrorCode code, String msg) {
        return new BizException(code, msg);
    }
}
