package com.yundao.bp.sys.audit;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.sys.service.AuditService;
import jakarta.servlet.http.HttpServletRequest;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/**
 * 审计切面。
 *
 * <p>记录：操作人、动作、入参摘要、返回值摘要、是否成功、客户端 IP。
 * <b>审计失败不影响主业务</b>（记警告日志，不抛出）。
 */
@Aspect
@Component
public class AuditAspect {

    private static final Logger log = LoggerFactory.getLogger(AuditAspect.class);
    private static final ObjectMapper JSON = new ObjectMapper();
    /** 单字段最大长度，防超长入参撑爆审计表 */
    private static final int MAX_LEN = 1800;

    private final AuditService auditService;

    public AuditAspect(AuditService auditService) {
        this.auditService = auditService;
    }

    @Around("@annotation(audit)")
    public Object around(ProceedingJoinPoint pjp, Audit audit) throws Throwable {
        String args = null;
        try {
            args = truncate(JSON.writeValueAsString(pjp.getArgs()));
        } catch (Exception ignored) {
            args = "[unserializable]";
        }
        MethodSignature sig = (MethodSignature) pjp.getSignature();
        String target = sig.getDeclaringType().getSimpleName() + "." + sig.getName();

        boolean success = false;
        String resultSummary = null;
        try {
            Object ret = pjp.proceed();
            success = true;
            if (audit.recordResult()) {
                try {
                    resultSummary = truncate(JSON.writeValueAsString(ret));
                } catch (Exception ignored) {
                    resultSummary = "[unserializable]";
                }
            }
            return ret;
        } catch (Throwable ex) {
            resultSummary = "EXCEPTION: " + ex.getMessage();
            throw ex;
        } finally {
            writeQuietly(audit, target, args, resultSummary, success);
        }
    }

    private void writeQuietly(Audit audit, String target, String args, String result,
                              boolean success) {
        try {
            LoginUser u = LoginUser.get();
            auditService.record(
                    audit.type(), audit.level(),
                    audit.bizType().isBlank() ? null : audit.bizType(), null,
                    u == null ? null : u.userId(),
                    u == null ? null : (u.realName() == null ? u.username() : u.realName()),
                    target, null,
                    audit.action() + (success ? "" : "（失败）"),
                    success ? null : wrapJson(args),
                    success ? wrapJson(result) : writeFailJson(result),
                    null, clientIp());
        } catch (Exception ex) {
            log.warn("写审计日志失败（不影响主业务）：{}", ex.getMessage());
        }
    }

    /**
     * 把任意文本包装成<b>合法 JSON 对象</b>。
     *
     * <p>为什么需要：`bp_sys_audit_log.before_json/after_json` 是 MySQL JSON 列，
     * 直接写入被截断的 JSON 串会报 `Invalid JSON text`，导致审计丢失。
     * 统一包成 `{"text": "..."}` 可保证合法，同时保留可读内容。
     */
    private static String wrapJson(String s) {
        if (s == null) {
            return null;
        }
        try {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("text", truncate(s));
            return JSON.writeValueAsString(m);
        } catch (Exception e) {
            return null;
        }
    }

    /** 失败信息包装（含异常原文）。 */
    private static String writeFailJson(String s) {
        try {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("error", truncate(s));
            return JSON.writeValueAsString(m);
        } catch (Exception e) {
            return null;
        }
    }

    private static String truncate(String s) {
        if (s == null) {
            return null;
        }
        return s.length() <= MAX_LEN ? s : s.substring(0, MAX_LEN) + "...(截断)";
    }

    private static String clientIp() {
        try {
            ServletRequestAttributes attrs =
                    (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attrs == null) {
                return null;
            }
            HttpServletRequest req = attrs.getRequest();
            String xf = req.getHeader("X-Forwarded-For");
            return xf != null && !xf.isBlank() ? xf.split(",")[0].trim() : req.getRemoteAddr();
        } catch (Exception e) {
            return null;
        }
    }
}
