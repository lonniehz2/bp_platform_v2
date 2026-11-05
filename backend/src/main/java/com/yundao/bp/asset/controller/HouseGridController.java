package com.yundao.bp.asset.controller;

import com.yundao.bp.asset.dto.HouseVO;
import com.yundao.bp.asset.service.HouseService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 房源台账格子视图聚合接口。 */
@RestController
@RequestMapping("/api/v1/houses")
public class HouseGridController {

    private final HouseService houseService;
    private final JdbcTemplate jdbc;

    public HouseGridController(HouseService houseService, JdbcTemplate jdbc) {
        this.houseService = houseService;
        this.jdbc = jdbc;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:house:view")
    @GetMapping("/grid")
    public R<PageResult<Map<String, Object>>> grid(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) Boolean includeChildren,
            @RequestParam(required = false) String houseStatus,
            @RequestParam(required = false) String houseType,
            @RequestParam(required = false) String keyword) {
        PageResult<HouseVO> page = houseService.page(pageNum, pageSize, orgId, spaceId,
                houseStatus, houseType, keyword, includeChildren);
        List<HouseVO> houses = page.rows();
        if (houses.isEmpty()) {
            return R.ok(PageResult.of(page.total(), pageNum, pageSize, List.of()));
        }
        List<Long> houseIds = houses.stream().map(HouseVO::id).toList();
        List<Long> spaceIds = houses.stream().map(HouseVO::spaceId)
                .filter(java.util.Objects::nonNull).distinct().toList();
        String hi = placeholders(houseIds.size());
        String si = placeholders(spaceIds.size());

        Map<Long, Integer> occupied = new HashMap<>();
        Map<Long, String> lessee = new HashMap<>();
        if (!houseIds.isEmpty()) {
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "select c.house_id houseId, c.lessee_name lesseeName, "
                            + "1 + (select count(*) from bp_biz_contract_cohabitant co "
                            + "where co.contract_id=c.id) people "
                            + "from bp_biz_contract c where c.is_deleted=0 "
                            + "and c.contract_status in ('EFFECTIVE','RENEWING') "
                            + "and c.house_id in (" + hi + ")", houseIds.toArray());
            for (Map<String, Object> r : rows) {
                Long hid = num(r.get("houseId"));
                occupied.merge(hid, ((Number) r.get("people")).intValue(), Integer::sum);
                lessee.putIfAbsent(hid, str(r.get("lesseeName")));
            }
        }

        Map<Long, List<Map<String, Object>>> devices = new HashMap<>();
        if (!spaceIds.isEmpty()) {
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "select id, space_id spaceId, device_id deviceId, device_name deviceName, "
                            + "device_type deviceType, device_mac deviceMac, online_status onlineStatus, "
                            + "battery, install_status installStatus "
                            + "from bp_dev_device where is_deleted=0 and space_id in (" + si + ")", spaceIds.toArray());
            for (Map<String, Object> r : rows) {
                devices.computeIfAbsent(num(r.get("spaceId")), k -> new ArrayList<>()).add(r);
            }
        }

        Map<Long, Integer> alerts = new HashMap<>();
        if (!houseIds.isEmpty()) {
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "select house_id houseId, count(*) n from bp_ops_alert "
                            + "where alert_status='PENDING' and house_id in (" + hi + ") group by house_id",
                    houseIds.toArray());
            for (Map<String, Object> r : rows) {
                alerts.put(num(r.get("houseId")), ((Number) r.get("n")).intValue());
            }
        }

        Map<Long, Map<String, Object>> freezes = new HashMap<>();
        if (!houseIds.isEmpty()) {
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "select house_id houseId, max(reason) reason, count(*) n from bp_grant_freeze "
                            + "where freeze_status in ('FREEZING','FROZEN') and house_id in (" + hi + ")"
                            + " group by house_id", houseIds.toArray());
            for (Map<String, Object> r : rows) {
                freezes.put(num(r.get("houseId")), r);
            }
        }

        List<Map<String, Object>> out = new ArrayList<>();
        for (HouseVO h : houses) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("houseId", String.valueOf(h.id()));
            m.put("houseCode", h.houseCode());
            m.put("houseName", h.houseName());
            m.put("spaceId", h.spaceId() == null ? null : String.valueOf(h.spaceId()));
            m.put("spaceFullName", h.spaceFullName());
            m.put("houseStatus", h.houseStatus());
            m.put("houseStatusLabel", h.houseStatusLabel());
            m.put("houseType", h.houseType());
            m.put("spaceType", h.spaceType());
            m.put("area", h.area());
            m.put("rentStandard", h.rentStandard());
            m.put("rentUnit", h.rentUnit());
            m.put("orgId", h.orgId() == null ? null : String.valueOf(h.orgId()));
            int cap = h.maxCapacity() == null || h.maxCapacity() <= 0 ? 1 : h.maxCapacity();
            m.put("capacity", cap);
            m.put("occupiedCount", occupied.getOrDefault(h.id(), 0));
            m.put("lesseeName", lessee.get(h.id()));
            m.put("alertCount", alerts.getOrDefault(h.id(), 0));
            Map<String, Object> f = freezes.get(h.id());
            m.put("frozen", f != null);
            m.put("freezeReason", f == null ? null : f.get("reason"));
            List<Map<String, Object>> ds = devices.getOrDefault(h.spaceId(), List.of());
            m.put("deviceCount", ds.size());
            Map<String, Object> lock = null;
            for (Map<String, Object> d : ds) {
                if ("LOCK".equals(d.get("deviceType"))) {
                    lock = d;
                    if ("1".equals(String.valueOf(d.get("onlineStatus")))) {
                        break;
                    }
                }
            }
            if (lock != null) {
                Map<String, Object> lm = new LinkedHashMap<>();
                lm.put("deviceId", str(lock.get("deviceId")));
                lm.put("deviceName", str(lock.get("deviceName")));
                lm.put("deviceMac", str(lock.get("deviceMac")));
                Object online = lock.get("onlineStatus");
                lm.put("onlineStatus", online instanceof Boolean b ? (b ? 1 : 0) : online);
                lm.put("battery", lock.get("battery"));
                lm.put("installStatus", str(lock.get("installStatus")));
                m.put("lock", lm);
            } else {
                m.put("lock", null);
            }
            out.add(m);
        }
        return R.ok(PageResult.of(page.total(), pageNum, pageSize, out));
    }

    private static String placeholders(int n) {
        return String.join(",", java.util.Collections.nCopies(n, "?"));
    }

    private static Long num(Object v) {
        return v == null ? null : ((Number) v).longValue();
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v);
    }
}
