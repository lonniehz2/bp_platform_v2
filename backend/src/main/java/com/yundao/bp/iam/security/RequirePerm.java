package com.yundao.bp.iam.security;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 声明接口所需权限。
 *
 * <p>加在 Controller 方法上，由 {@link AuthInterceptor} 校验；不标注则仅要求登录。
 */
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface RequirePerm {

    /** 权限标识码，如 `asset:house:edit`。 */
    String value();
}
