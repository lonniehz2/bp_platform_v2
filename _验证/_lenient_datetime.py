# -*- coding: utf-8 -*-
"""消除时间格式技术债：LocalDateTime 反序列化同时接受
   · "2026-11-05 14:00:00"（既有约定）
   · "2026-11-05T14:00:00"（ISO 8601，前端/第三方常用）
   · "2026-11-05T14:00:00.000Z" / 带毫秒
   · "2026-11-05"（只传日期，按当天 00:00:00）

序列化保持 yyyy-MM-dd HH:mm:ss 不变，避免影响既有前端展示。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'common', 'config', 'JacksonConfig.java')
s = io.open(P, encoding='utf-8').read()

if 'LenientLocalDateTimeDeserializer' not in s:
    helper = '''
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

'''
    s = s.replace('    @Bean\n    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {',
                  helper + '    @Bean\n    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {', 1)
    s = s.replace('time.addDeserializer(LocalDateTime.class, new LocalDateTimeDeserializer(dtf));',
                  'time.addDeserializer(LocalDateTime.class, new LenientLocalDateTimeDeserializer());', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('JacksonConfig：已加宽松时间反序列化')
else:
    print('已存在')
