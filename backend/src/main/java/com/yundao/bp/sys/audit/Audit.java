package com.yundao.bp.sys.audit;

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
