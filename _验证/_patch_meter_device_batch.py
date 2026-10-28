# -*- coding: utf-8 -*-
"""抄表：按房源+计费项带出设备；批量录入接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

p = os.path.join(BE, 'fin', 'controller', 'MeterReadingController.java')
s = io.open(p, encoding='utf-8').read()
if 'devices' not in s:
    s = s.replace('''    @PostMapping
    @RequirePerm("fin:bill:create")
    public R<FinMeterReading> record(@Valid @RequestBody MeterReadingCmd cmd) {
        return R.ok(service.record(cmd));
    }''', '''    @PostMapping
    @RequirePerm("fin:bill:create")
    public R<FinMeterReading> record(@Valid @RequestBody MeterReadingCmd cmd) {
        return R.ok(service.record(cmd));
    }

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;

    /**
     * 房源 + 计费项目下的计量设备（同项目多设备时逐台录入）。
     */
    @RequirePerm("fin:bill:view")
    @GetMapping("/devices")
    public R<java.util.List<java.util.Map<String, Object>>> devices(
            @RequestParam Long houseId, @RequestParam Long feeItemId) {
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        if (jdbc == null) {
            return R.ok(out);
        }
        java.util.List<String> codes = jdbc.queryForList(
                "select concat(coalesce(item_code,''),'|',coalesce(item_type,'')) "
                        + "from bp_fin_fee_item where id = ?", String.class, feeItemId);
        String meterType = null;
        if (!codes.isEmpty() && codes.get(0) != null) {
            String code = codes.get(0).toUpperCase();
            if (code.contains("ELEC") || code.contains("电")) {
                meterType = "ELEC_METER";
            } else if (code.contains("WATER") || code.contains("水")) {
                meterType = "WATER_METER";
            } else if (code.contains("GAS") || code.contains("气")) {
                meterType = "GAS_METER";
            } else if (code.contains("HEAT") || code.contains("热")) {
                meterType = "HEAT_METER";
            }
        }
        java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                "select d.device_id, d.device_name, d.device_type, s.space_name "
                        + "from bp_dev_device d "
                        + "join bp_asset_house h on h.space_id = d.space_id "
                        + "left join bp_asset_space s on s.id = d.space_id "
                        + "where h.id = ? "
                        + (meterType == null ? "" : "and d.device_type = ? ")
                        + "order by d.device_type, d.device_id",
                meterType == null
                        ? new Object[]{houseId}
                        : new Object[]{houseId, meterType});
        out.addAll(rows);
        return R.ok(out);
    }

    /** 批量录入（每行一条读数）。 */
    @PostMapping("/batch")
    @RequirePerm("fin:bill:create")
    public R<java.util.Map<String, Object>> batch(@RequestBody java.util.List<MeterReadingCmd> cmds) {
        int ok = 0;
        java.util.List<java.util.Map<String, Object>> errors = new java.util.ArrayList<>();
        int line = 0;
        for (MeterReadingCmd cmd : cmds) {
            line++;
            try {
                service.record(cmd);
                ok++;
            } catch (Exception e) {
                java.util.Map<String, Object> er = new java.util.LinkedHashMap<>();
                er.put("line", line);
                er.put("message", e.getMessage());
                errors.add(er);
            }
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("total", cmds.size());
        out.put("created", ok);
        out.put("failed", errors.size());
        out.put("errors", errors);
        return R.ok(out);
    }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('抄表设备/批量接口已加')
