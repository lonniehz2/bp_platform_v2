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
            time.addDeserializer(LocalDateTime.class, new LocalDateTimeDeserializer(dtf));
            time.addSerializer(LocalDate.class, new LocalDateSerializer(df));
            time.addDeserializer(LocalDate.class, new LocalDateDeserializer(df));

            builder.modules(longToString, time);
        };
    }
}
