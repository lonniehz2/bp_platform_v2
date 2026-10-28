# -*- coding: utf-8 -*-
"""抄表导出模板接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'fin', 'controller', 'MeterReadingController.java')
s = io.open(p, encoding='utf-8').read()
if 'export-template' not in s:
    s = s.replace('''    /** 批量录入（每行一条读数）。 */''', '''    /**
     * 导出抄表模板：按组织/空间（含下级）+ 计量项目生成房源与设备行，读数留空。
     */
    @RequirePerm("fin:bill:view")
    @GetMapping("/export-template")
    public R<java.util.List<java.util.Map<String, Object>>> exportTemplate(
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) Long spaceId,
            @RequestParam Long feeItemId) {
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        if (jdbc == null) {
            return R.ok(out);
        }
        java.util.List<String> codeRows = jdbc.queryForList(
                "select concat(coalesce(item_code,''),'|',coalesce(item_name,'')) "
                        + "from bp_fin_fee_item where id = ?", String.class, feeItemId);
        String itemText = codeRows.isEmpty() ? "" : codeRows.get(0).toUpperCase();
        String meterType = null;
        if (itemText.contains("ELEC") || itemText.contains("电")) {
            meterType = "ELEC_METER";
        } else if (itemText.contains("WATER") || itemText.contains("水")) {
            meterType = "WATER_METER";
        } else if (itemText.contains("GAS") || itemText.contains("气")) {
            meterType = "GAS_METER";
        } else if (itemText.contains("HEAT") || itemText.contains("热")) {
            meterType = "HEAT_METER";
        }
        StringBuilder sql = new StringBuilder(
                "select o.org_name, s.space_name, h.house_code, h.house_name, "
                        + "fi.item_name, d.device_id, d.device_name, d.device_type, "
                        + "s.space_path, s.id as space_id "
                        + "from bp_asset_house h "
                        + "join bp_asset_space s on s.id = h.space_id "
                        + "left join bp_iam_org o on o.id = h.org_id "
                        + "join bp_fin_fee_item fi on fi.id = ? "
                        + "left join bp_dev_device d on d.space_id = h.space_id "
                        + (meterType == null ? "" : "and d.device_type = '" + meterType + "' ")
                        + "where h.is_deleted = 0 ");
        java.util.List<Object> args = new java.util.ArrayList<>();
        args.add(feeItemId);
        if (orgId != null) {
            sql.append("and h.org_id = ? ");
            args.add(orgId);
        }
        if (spaceId != null) {
            sql.append("and h.space_id in (select id from bp_asset_space where id = ? ")
                    .append("or space_path like concat((select space_path from bp_asset_space ")
                    .append("where id = ?), '%')) ");
            args.add(spaceId);
            args.add(spaceId);
        }
        sql.append("order by h.house_code, d.device_type, d.device_id");
        java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                sql.toString(), args.toArray());
        for (java.util.Map<String, Object> r : rows) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("orgName", r.get("org_name"));
            m.put("spaceName", r.get("space_name"));
            m.put("houseCode", r.get("house_code"));
            m.put("houseName", r.get("house_name"));
            m.put("feeItemName", r.get("item_name"));
            m.put("deviceId", r.get("device_id"));
            m.put("deviceName", r.get("device_name"));
            m.put("deviceType", r.get("device_type"));
            m.put("reading", "");
            m.put("readDate", java.time.LocalDate.now().toString());
            out.add(m);
        }
        return R.ok(out);
    }

    /** 批量录入（每行一条读数）。 */''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('导出模板接口已加')
