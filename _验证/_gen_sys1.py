# -*- coding: utf-8 -*-
"""生成 sys 支撑层：实体 + Mapper + 服务 + AOP 审计"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== 实体 ====================
F['sys/entity/SysDict.java'] = '''package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 数据字典。对应 `bp_sys_dict`。
 *
 * <p>租户级可覆盖系统内置：{@code tenant_id} 为空表示系统内置。
 */
@Data
@TableName("bp_sys_dict")
public class SysDict {

    @TableId(type = IdType.INPUT)
    private Long id;

    /** 租户ID（NULL 表示系统内置） */
    private String tenantId;
    private String dictType;
    private String dictCode;
    private String dictLabel;
    private String dictValue;
    private Integer sortNo;
    private String cssClass;
    private Integer isDefault;
    /** ENABLED / DISABLED */
    private String dictStatus;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

F['sys/entity/SysConfig.java'] = '''package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 系统参数。对应 `bp_sys_config`。
 *
 * <p>用途：把政策参数（公示天数、禁申年限、过渡期月数、加价倍率等）
 * 从硬编码改为可配置，支持分地区差异。
 */
@Data
@TableName("bp_sys_config")
public class SysConfig {

    @TableId(type = IdType.INPUT)
    private Long id;

    /** 租户ID（NULL 表示全局） */
    private String tenantId;
    private String configKey;
    private String configValue;
    /** SYSTEM / BUSINESS / IOT / NOTIFY / SECURITY */
    private String configGroup;
    /** STRING / INT / DECIMAL / BOOL / JSON */
    private String valueType;
    private Integer isEncrypted;
    private Integer isSystem;
    private String description;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
'''

F['sys/entity/SysAuditLog.java'] = '''package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 审计日志。对应 `bp_sys_audit_log`。
 *
 * <p><b>只追加不可修改</b>：不提供 update/delete 接口，
 * 保证关键动作（授权/资金/审核/权限）可追溯且不可篡改。
 */
@Data
@TableName("bp_sys_audit_log")
public class SysAuditLog {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    /** GRANT / FINANCE / REVIEW / PERMISSION / DATA / OTHER */
    private String auditType;
    /** CRITICAL / IMPORTANT / NORMAL */
    private String auditLevel;

    private String bizType;
    private Long bizId;

    private Long operatorId;
    private String operatorName;

    private String targetType;
    private String targetId;
    private String action;

    private String beforeJson;
    private String afterJson;
    private String reason;
    private String clientIp;

    private LocalDateTime auditTime;
    private LocalDateTime createTime;
}
'''

for n in ('SysDict', 'SysConfig', 'SysAuditLog'):
    F['sys/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.sys.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.sys.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== 审计注解 + AOP ====================
F['sys/audit/Audit.java'] = '''package com.yundao.bp.sys.audit;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 声明需要审计的关键操作。
 *
 * <p>加在 Controller 方法上，由 {@link AuditAspect} 自动落 `bp_sys_audit_log`。
 *
 * <pre>
 * &#64;Audit(type = "FINANCE", level = "CRITICAL", action = "批量出账")
 * </pre>
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Audit {

    /** 审计类型：GRANT / FINANCE / REVIEW / PERMISSION / DATA / OTHER */
    String type() default "OTHER";

    /** 级别：CRITICAL / IMPORTANT / NORMAL */
    String level() default "NORMAL";

    /** 动作描述，如「批量出账」「记入失信」 */
    String action();

    /** 业务类型（可选），如 CONTRACT / BILL */
    String bizType() default "";

    /** 是否记录返回值（默认记录摘要） */
    boolean recordResult() default true;
}
'''

F['sys/audit/AuditAspect.java'] = '''package com.yundao.bp.sys.audit;

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
                    success ? null : args,
                    result,
                    null, clientIp());
        } catch (Exception ex) {
            log.warn("写审计日志失败（不影响主业务）：{}", ex.getMessage());
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
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
