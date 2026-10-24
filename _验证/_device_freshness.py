# -*- coding: utf-8 -*-
"""设备数据新鲜度：把「上报频率」契约变成可检查的接口。

规则（参考泊寓接入条件）：
  门锁电量 ≥ 1 天 1 次；水电表用量 ≥ 1 天 2 次；网络状态误差 ≤ 30 分钟
判定：last_report_time 超过阈值即视为「数据失联」。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'dev')

# 实体字段
E = os.path.join(J, 'entity', 'DevDevice.java')
s = io.open(E, encoding='utf-8').read()
if 'lastReportTime' not in s:
    s = s.replace('    private LocalDateTime offlineTime;',
                  '    private LocalDateTime offlineTime;\n\n'
                  '    /** 最后一次上报时间（属性/事件/心跳均可刷新） */\n'
                  '    private LocalDateTime lastReportTime;', 1)
    io.open(E, 'w', encoding='utf-8', newline='').write(s)
    print('DevDevice：lastReportTime 已加')

# 控制器接口
C = os.path.join(J, 'controller', 'DeviceController.java')
s = io.open(C, encoding='utf-8').read()
if 'freshness' not in s:
    block = '''
    /**
     * 数据新鲜度检查：按上报间隔契约判定设备是否失联。
     *
     * <p>门锁要求 ≥1 天 1 次、水电表 ≥1 天 2 次；传入 hours 可自定义阈值。
     * 用于上线后巡检「数据静默失效」。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/freshness")
    public R<java.util.Map<String, Object>> freshness(
            @RequestParam(defaultValue = "24") int hours) {
        java.time.LocalDateTime deadline = java.time.LocalDateTime.now()
                .minusHours(Math.max(1, hours));
        java.util.List<DevDevice> all = mapper.selectList(new LambdaQueryWrapper<>());
        java.util.List<java.util.Map<String, Object>> stale = new java.util.ArrayList<>();
        int fresh = 0;
        for (DevDevice d : all) {
            java.time.LocalDateTime last = d.getLastReportTime() != null
                    ? d.getLastReportTime()
                    : (d.getUpdateTime() != null ? d.getUpdateTime() : d.getCreateTime());
            boolean ok = last != null && last.isAfter(deadline);
            if (ok) {
                fresh++;
                continue;
            }
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("deviceId", d.getDeviceId());
            m.put("deviceName", d.getDeviceName());
            m.put("deviceType", d.getDeviceType());
            m.put("spaceId", d.getSpaceId() == null ? null : String.valueOf(d.getSpaceId()));
            m.put("lastReportTime", last == null ? null : last.toString());
            m.put("hoursSilent", last == null ? null
                    : java.time.Duration.between(last, java.time.LocalDateTime.now()).toHours());
            m.put("battery", d.getBattery());
            stale.add(m);
        }
        stale.sort((a, b) -> Long.compare(
                ((Number) (b.get("hoursSilent") == null ? 0 : b.get("hoursSilent"))).longValue(),
                ((Number) (a.get("hoursSilent") == null ? 0 : a.get("hoursSilent"))).longValue()));
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("thresholdHours", hours);
        out.put("total", all.size());
        out.put("fresh", fresh);
        out.put("stale", stale.size());
        out.put("staleRate", all.isEmpty() ? 0.0
                : Math.round(stale.size() * 10000.0 / all.size()) / 100.0);
        out.put("staleDevices", stale.size() > 50 ? stale.subList(0, 50) : stale);
        return R.ok(out);
    }
'''
    anchor = '    /** 在线/绑定状态统计（看板用）。 */'
    s = s.replace(anchor, block + '\n' + anchor, 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('DeviceController：/freshness 已加')

print('完成')
