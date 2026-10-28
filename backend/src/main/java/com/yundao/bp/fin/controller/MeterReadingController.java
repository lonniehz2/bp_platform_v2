package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.MeterReadingCmd;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.service.MeterReadingService;
import com.yundao.bp.iam.security.RequirePerm;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 能耗抄表（水电燃气）。 */
@RestController
@RequestMapping("/api/v1/fin/meter-readings")
public class MeterReadingController {

    private final MeterReadingService service;

    public MeterReadingController(MeterReadingService service) {
        this.service = service;
    }

    @PostMapping
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

    /**
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
    }

    @GetMapping
    @RequirePerm("fin:bill:view")
    public R<PageResult<FinMeterReading>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) Long feeItemId) {
        return R.ok(service.page(pageNum, pageSize, houseId, feeItemId));
    }

    /** 按读数生成账单。 */
    @PostMapping("/{id}/bill")
    @RequirePerm("fin:bill:create")
    public R<BillVO> bill(@PathVariable Long id) {
        return R.ok(service.bill(id));
    }

    /** 能耗分析：月度用量/金额 + 楼栋与房源排名。 */
    @GetMapping("/analytics")
    public R<java.util.Map<String, Object>> analytics(
            @RequestParam(required = false) Long orgId,
            @RequestParam(defaultValue = "6") int months) {
        return R.ok(service.analytics(orgId, months));
    }
}
