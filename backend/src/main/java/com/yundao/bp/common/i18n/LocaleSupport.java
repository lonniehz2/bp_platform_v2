package com.yundao.bp.common.i18n;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Locale;

/** 语言标签解析：X-Locale 优先，其次 Accept-Language；首期支持 zh-CN / en-US。 */
public final class LocaleSupport {

    private LocaleSupport() {
    }

    public static Locale fromRequest(HttpServletRequest request) {
        String explicit = request.getHeader("X-Locale");
        if (explicit != null && !explicit.isBlank()) {
            return normalize(explicit);
        }
        String accept = request.getHeader("Accept-Language");
        if (accept != null && !accept.isBlank()) {
            for (String part : accept.split(",")) {
                String tag = part.split(";")[0].trim();
                if (tag.startsWith("en")) {
                    return Locale.US;
                }
                if (tag.startsWith("zh")) {
                    return Locale.SIMPLIFIED_CHINESE;
                }
            }
        }
        return LocaleContext.DEFAULT;
    }

    public static Locale normalize(String tag) {
        if (tag == null) {
            return LocaleContext.DEFAULT;
        }
        String t = tag.trim().replace('_', '-').toLowerCase(Locale.ROOT);
        if (t.startsWith("en")) {
            return Locale.US;
        }
        return Locale.SIMPLIFIED_CHINESE;
    }
}
