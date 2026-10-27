# -*- coding: utf-8 -*-
"""回调批量重放（断线补推/失败重试）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iot',
                 'gateway', 'IotToolController.java')
s = io.open(p, encoding='utf-8').read()

if 'replay-range' not in s:
    # 抽公共方法
    s = s.replace('''        String ts = String.valueOf(System.currentTimeMillis() / 1000);
        String nonce = "replay" + id + ts;
        String appId = settings.getString("iot.callback.appId");
        String secret = settings.getString("iot.callback.appSecret");
        String path = "/api/callback/iot/" + l.getMsgType();
        String body = l.getRawBody() == null ? "{}" : l.getRawBody();
        String signature = hmac(secret, "POST\\n" + path + "\\n" + appId + "\\n" + ts
                + "\\n" + nonce + "\\n" + IotSignatureVerifier.sha256Hex(body));
        IotCallbackService.Reply reply = callbackService.handle(l.getMsgType(), body,
                appId, ts, nonce, signature, "127.0.0.1", l.getTenantId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("httpStatus", reply.httpStatus());
        out.put("code", reply.code());
        out.put("message", reply.message());
        return R.ok(out);
    }''', '''        return R.ok(replayOne(l));
    }

    /**
     * 批量重放：断线补推 / 失败重试。
     *
     * @param from 接收时间起（yyyy-MM-dd HH:mm:ss）
     * @param to   接收时间止
     * @param status 处理状态，默认 FAILED；ALL 表示不限
     * @param limit 最多重放条数（≤200）
     */
    @RequirePerm("dev:command:retry")
    @PostMapping("/callback-logs/replay-range")
    public R<Map<String, Object>> replayRange(
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(defaultValue = "FAILED") String status,
            @RequestParam(defaultValue = "100") int limit) {
        java.time.LocalDateTime start = parseTime(from,
                java.time.LocalDateTime.now().minusDays(1));
        java.time.LocalDateTime end = parseTime(to, java.time.LocalDateTime.now());
        int cap = Math.max(1, Math.min(limit, 200));
        LambdaQueryWrapper<IotCallbackLog> qw = new LambdaQueryWrapper<IotCallbackLog>()
                .ge(IotCallbackLog::getReceiveTime, start)
                .le(IotCallbackLog::getReceiveTime, end)
                .eq(!"ALL".equalsIgnoreCase(status) && status != null && !status.isBlank(),
                        IotCallbackLog::getProcessStatus, status)
                .orderByAsc(IotCallbackLog::getReceiveTime)
                .last("LIMIT " + cap);
        java.util.List<IotCallbackLog> logs = logMapper.selectList(qw);
        int success = 0;
        int failed = 0;
        java.util.List<Map<String, Object>> details = new java.util.ArrayList<>();
        for (IotCallbackLog l : logs) {
            Map<String, Object> one = replayOne(l);
            one.put("id", l.getId());
            one.put("msgType", l.getMsgType());
            boolean ok = one.get("httpStatus") instanceof Integer code && code == 200;
            if (ok) {
                success++;
            } else {
                failed++;
            }
            if (details.size() < 20) {
                details.add(one);
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("from", start.toString());
        out.put("to", end.toString());
        out.put("status", status);
        out.put("matched", logs.size());
        out.put("success", success);
        out.put("failed", failed);
        out.put("details", details);
        return R.ok(out);
    }

    private Map<String, Object> replayOne(IotCallbackLog l) {
        String ts = String.valueOf(System.currentTimeMillis() / 1000);
        String nonce = "replay" + l.getId() + ts;
        String appId = settings.getString("iot.callback.appId");
        String secret = settings.getString("iot.callback.appSecret");
        String path = "/api/callback/iot/" + l.getMsgType();
        String body = l.getRawBody() == null ? "{}" : l.getRawBody();
        String signature = hmac(secret, "POST\\n" + path + "\\n" + appId + "\\n" + ts
                + "\\n" + nonce + "\\n" + IotSignatureVerifier.sha256Hex(body));
        IotCallbackService.Reply reply = callbackService.handle(l.getMsgType(), body,
                appId, ts, nonce, signature, "127.0.0.1", l.getTenantId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("httpStatus", reply.httpStatus());
        out.put("code", reply.code());
        out.put("message", reply.message());
        return out;
    }

    private static java.time.LocalDateTime parseTime(String text,
                                                     java.time.LocalDateTime fallback) {
        if (text == null || text.isBlank()) {
            return fallback;
        }
        try {
            return java.time.LocalDateTime.parse(text.trim().replace(' ', 'T'));
        } catch (Exception e) {
            return fallback;
        }
    }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('批量重放已加')
