package com.yundao.bp.common.config;

import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.ser.std.ToStringSerializer;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateDeserializer;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateSerializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Jackson 序列化配置。
 *
 * <p><b>两条硬性约定</b>（见 {@code 03_API契约.md} §1）：
 * <ol>
 *   <li><b>Long / BigDecimal 序列化为字符串</b>：雪花 ID 超过 JS 安全整数（2^53），
 *       金额用字符串避免浮点误差。</li>
 *   <li>时间统一 {@code yyyy-MM-dd HH:mm:ss}，日期 {@code yyyy-MM-dd}。</li>
 * </ol>
 */
@Configuration
public class JacksonConfig {

    public static final String DATE_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss";
    public static final String DATE_PATTERN = "yyyy-MM-dd";


    /**
     * 宽松时间反序列化：兼容空格与 ISO 两种写法，避免前端传 T 分隔就 500。
     */
    static class LenientLocalDateTimeDeserializer
            extends com.fasterxml.jackson.databind.JsonDeserializer<LocalDateTime> {

        private static final DateTimeFormatter SPACE = DateTimeFormatter.ofPattern(DATE_TIME_PATTERN);

        @Override
        public LocalDateTime deserialize(com.fasterxml.jackson.core.JsonParser p,
                                         com.fasterxml.jackson.databind.DeserializationContext ctx)
                throws java.io.IOException {
            String text = p.getText();
            if (text == null || text.isBlank()) {
                return null;
            }
            String v = text.trim();
            try {
                if (v.length() == 10) {
                    return LocalDate.parse(v).atStartOfDay();   // 只给日期
                }
                if (v.indexOf('T') > 0) {
                    String n = v.replace('Z', ' ');
                    if (n.endsWith(" ")) {
                        n = n.trim();
                    }
                    if (n.length() > 19) {
                        n = n.substring(0, 19);                 // 去掉毫秒/时区
                    }
                    return LocalDateTime.parse(n.replace('T', ' '), SPACE);
                }
                if (v.length() > 19) {
                    v = v.substring(0, 19);
                }
                return LocalDateTime.parse(v, SPACE);
            } catch (Exception ex) {
                throw new java.io.IOException("时间格式无法解析：" + text
                        + "（支持 yyyy-MM-dd HH:mm:ss 或 ISO 2026-11-05T14:00:00）", ex);
            }
        }
    }

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> {
            SimpleModule longToString = new SimpleModule();
            // 只序列化为字符串，反序列化仍按数字/字符串皆可（Jackson 默认支持）
            longToString.addSerializer(Long.class, ToStringSerializer.instance);
            longToString.addSerializer(Long.TYPE, ToStringSerializer.instance);
            longToString.addSerializer(BigDecimal.class, ToStringSerializer.instance);

            DateTimeFormatter dtf = DateTimeFormatter.ofPattern(DATE_TIME_PATTERN);
            DateTimeFormatter df = DateTimeFormatter.ofPattern(DATE_PATTERN);
            JavaTimeModule time = new JavaTimeModule();
            time.addSerializer(LocalDateTime.class, new LocalDateTimeSerializer(dtf));
            time.addDeserializer(LocalDateTime.class, new LenientLocalDateTimeDeserializer());
            time.addSerializer(LocalDate.class, new LocalDateSerializer(df));
            time.addDeserializer(LocalDate.class, new LocalDateDeserializer(df));

            builder.modules(longToString, time);
        };
    }
}
