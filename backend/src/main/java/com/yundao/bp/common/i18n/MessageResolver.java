package com.yundao.bp.common.i18n;

import com.yundao.bp.common.api.ErrorCode;
import java.util.Locale;
import org.springframework.context.MessageSource;
import org.springframework.stereotype.Component;

/** 统一消息解析：key + args + 当前 Locale；缺失时回退默认文案。 */
@Component
public class MessageResolver {

    private final MessageSource messageSource;

    public MessageResolver(MessageSource messageSource) {
        this.messageSource = messageSource;
    }

    public String get(String key, Object... args) {
        return get(key, key, args);
    }

    public String get(String key, String defaultMessage, Object... args) {
        return messageSource.getMessage(key, args, defaultMessage, LocaleContext.get());
    }

    public String error(ErrorCode errorCode) {
        return get(errorCode.messageKey(), errorCode.message());
    }

    public String localized(String detail, ErrorCode errorCode) {
        if (!LocaleContext.isEnglish() && detail != null && !detail.isBlank()) {
            return detail;
        }
        return error(errorCode);
    }
}
