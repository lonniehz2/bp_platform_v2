package com.yundao.bp.common.i18n;

import com.alibaba.ttl.TransmittableThreadLocal;
import java.util.Locale;

/** 当前请求语言；必须在线程池/异步场景中传递，并在 finally 中清理。 */
public final class LocaleContext {

    public static final Locale DEFAULT = Locale.SIMPLIFIED_CHINESE;

    private static final ThreadLocal<Locale> HOLDER = new TransmittableThreadLocal<>();

    private LocaleContext() {
    }

    public static void set(Locale locale) {
        HOLDER.set(locale == null ? DEFAULT : locale);
    }

    public static Locale get() {
        Locale locale = HOLDER.get();
        return locale == null ? DEFAULT : locale;
    }

    public static String tag() {
        Locale locale = get();
        return "en".equalsIgnoreCase(locale.getLanguage()) ? "en-US" : "zh-CN";
    }

    public static boolean isEnglish() {
        return "en".equalsIgnoreCase(get().getLanguage());
    }

    public static void clear() {
        HOLDER.remove();
    }
}
