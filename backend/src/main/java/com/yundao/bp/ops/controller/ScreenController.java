package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.R;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 可视化大屏：小区/楼栋联动、房间状态墙、房源与年龄统计。 */
@RestController
@RequestMapping("/api/v1/screen")
public class ScreenController {

    private final JdbcTemplate jdbc;

    public ScreenController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:house:view")
    @GetMapping("/overview")
    public R<Map<String, Object>> overview(
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) Long buildingId) {
        Map<String, Object> out = new LinkedHashMap<>();
        List<Map<String, Object>> communities = jdbc.queryForList(
                "select distinct o.id, o.org_name as name from bp_iam_org o "
                        + "join bp_asset_house h on h.org_id = o.id and h.is_deleted = 0 "
                        + "where o.is_deleted = 0 order by o.org_name limit 100");
        out.put("communities", communities);

        List<Map<String, Object>> buildings = jdbc.queryForList(
                "select id, space_name as name from bp_asset_space "
                        + "where space_type = 'BUILDING' and is_deleted = 0 "
                        + "and (? is null or org_id = ?) order by sort_no, space_name limit 200",
                orgId, orgId);
        out.put("buildings", buildings);

        String spaceFilter = "";
        Object[] spaceArgs = new Object[]{};
        if (buildingId != null) {
            List<Map<String, Object>> bs = jdbc.queryForList(
                    "select space_path from bp_asset_space where id = ?", buildingId);
            String path = bs.isEmpty() || bs.get(0).get("space_path") == null
                    ? "" : String.valueOf(bs.get(0).get("space_path"));
            String prefix = path.isBlank() ? buildingId + "/" : path;
            spaceFilter = " and (h.space_id = ? or h.space_id in "
                    + "(select id from bp_asset_space where space_path like concat(?, '%'))) ";
            spaceArgs = new Object[]{buildingId, prefix};
        }
        String orgFilter = orgId == null ? "" : " and h.org_id = ? ";
        List<Object> args = new ArrayList<>();
        if (orgId != null) {
            args.add(orgId);
        }
        for (Object a : spaceArgs) {
            args.add(a);
        }
        List<Map<String, Object>> rooms = jdbc.queryForList(
                "select h.id, h.house_code as houseCode, h.house_name as houseName, "
                        + "h.house_status as houseStatus, h.space_id as spaceId, "
                        + "(select p.person_name from bp_biz_contract c "
                        + " join bp_person p on p.id = c.lessee_person_id "
                        + " where c.house_id = h.id and c.contract_status = 'EFFECTIVE' "
                        + " and c.is_deleted = 0 order by c.id desc limit 1) as personName, "
                        + "exists(select 1 from bp_ops_alert a where a.house_id = h.id "
                        + " and a.alert_status = 'PENDING') as hasAlert "
                        + "from bp_asset_house h where h.is_deleted = 0 "
                        + orgFilter + spaceFilter
                        + "order by h.house_code limit 800",
                args.toArray());
        int occupied = 0, vacant = 0, pending = 0, allocated = 0, disabled = 0;
        for (Map<String, Object> r : rooms) {
            String st = String.valueOf(r.get("houseStatus"));
            if ("OCCUPIED".equals(st)) {
                occupied++;
            } else if ("VACANT".equals(st) || "PENDING_ALLOC".equals(st)) {
                pending++;
                if ("VACANT".equals(st)) {
                    vacant++;
                }
            } else if ("ALLOCATED".equals(st) || "LOCKED".equals(st)) {
                allocated++;
            } else if ("DISABLED".equals(st) || "MAINTENANCE".equals(st)) {
                disabled++;
            }
        }
        int total = rooms.size();
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("total", total);
        stats.put("occupied", occupied);
        stats.put("vacant", vacant);
        stats.put("pending", pending);
        stats.put("allocated", allocated);
        stats.put("disabled", disabled);
        stats.put("occupancyRate", total == 0 ? 0
                : Math.round(occupied * 1000.0 / total) / 10.0);
        out.put("stats", stats);
        out.put("rooms", rooms);

        String ageWhere = "c.contract_status = 'EFFECTIVE' and c.is_deleted = 0 "
                + "and c.lessee_person_id is not null "
                + (orgId == null ? "" : "and c.org_id = ? ")
                + (buildingId == null ? "" : "and c.house_id in (select h.id from bp_asset_house h "
                + "where h.is_deleted = 0 " + spaceFilter.replace("h.space_id", "h.space_id") + ") ");
        List<Object> ageArgs = new ArrayList<>();
        if (orgId != null) {
            ageArgs.add(orgId);
        }
        if (buildingId != null) {
            for (Object a : spaceArgs) {
                ageArgs.add(a);
            }
        }
        List<Map<String, Object>> ages = jdbc.queryForList(
                "select case "
                        + " when p.birthday is null then 'UNKNOWN' "
                        + " when timestampdiff(year, p.birthday, curdate()) < 30 then 'LT30' "
                        + " when timestampdiff(year, p.birthday, curdate()) < 40 then 'AGE30_39' "
                        + " when timestampdiff(year, p.birthday, curdate()) < 50 then 'AGE40_49' "
                        + " when timestampdiff(year, p.birthday, curdate()) < 60 then 'AGE50_59' "
                        + " else 'AGE60_PLUS' end as label, count(distinct c.id) as count "
                        + "from bp_biz_contract c join bp_person p on p.id = c.lessee_person_id "
                        + "where " + ageWhere + " group by label", ageArgs.toArray());
        out.put("ageBuckets", ages);
        out.put("generatedAt", LocalDate.now().toString());
        return R.ok(out);
    }


}
