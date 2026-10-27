# -*- coding: utf-8 -*-
"""IoT 参数缓存（3s TTL）+ 改配置即时失效。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

p = os.path.join(BE, 'iot', 'config', 'IotSettings.java')
s = io.open(p, encoding='utf-8').read()
if 'invalidate()' not in s:
    s = s.replace('''    public String getString(String key) {
        String fallback = DEFAULTS.get(key);
        try {
            String v = configService.getString(key, fallback);
            return (v == null || v.isBlank()) ? fallback : v.trim();
        } catch (Exception e) {
            return fallback;
        }
    }''', '''    /** 回调热路径上参数读取频繁，加 3 秒缓存，避免每次回调多次查库。 */
    private final java.util.Map<String, Cached> cache = new java.util.concurrent.ConcurrentHashMap<>();
    private static final long TTL_MS = 3000;

    private record Cached(String value, long expireAt) {
    }

    /** 修改参数后调用，立即生效。 */
    public void invalidate() {
        cache.clear();
    }

    public String getString(String key) {
        String fallback = DEFAULTS.get(key);
        Cached c = cache.get(key);
        long now = System.currentTimeMillis();
        if (c != null && c.expireAt() > now) {
            return c.value();
        }
        try {
            String v = configService.getString(key, fallback);
            String value = (v == null || v.isBlank()) ? fallback : v.trim();
            if (value != null) {
                cache.put(key, new Cached(value, now + TTL_MS));
            }
            return value;
        } catch (Exception e) {
            return fallback;
        }
    }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('IotSettings 已加缓存')

p = os.path.join(BE, 'sys', 'controller', 'SysController.java')
s = io.open(p, encoding='utf-8').read()
if 'IotSettings' not in s:
    s = s.replace('''    private final ConfigService configService;

    public SysController(AuditService auditService, DictService dictService,
                         ConfigService configService) {''',
                  '''    private final ConfigService configService;
    private final com.yundao.bp.iot.config.IotSettings iotSettings;

    public SysController(AuditService auditService, DictService dictService,
                         ConfigService configService,
                         com.yundao.bp.iot.config.IotSettings iotSettings) {''', 1)
    s = s.replace('''        this.configService = configService;
    }''', '''        this.configService = configService;
        this.iotSettings = iotSettings;
    }''', 1)
    s = s.replace('''        return R.ok(configService.set(cmd.key(), cmd.value(), cmd.description()));''',
                  '''        SysConfig saved = configService.set(cmd.key(), cmd.value(), cmd.description());
        // 联调参数改完立即生效，不等缓存过期
        iotSettings.invalidate();
        return R.ok(saved);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('SysController 已联动失效')
