# -*- coding: utf-8 -*-
"""日房态合同占用 + 房源入住信息接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 日房态：合同区间已出租，区间外空置 ----------
p = os.path.join(BE, 'asset', 'service', 'impl', 'HouseCalendarServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'overlayContracts' not in s:
    s = s.replace('''    private List<DayCellVO> cells(Long houseId, LocalDate start, LocalDate end) {
        return loadRows(houseId, start, end).stream().map(this::toCell).toList();
    }''', '''    private List<DayCellVO> cells(Long houseId, LocalDate start, LocalDate end) {
        List<DayCellVO> list = loadRows(houseId, start, end).stream()
                .map(this::toCell).toList();
        return overlayContracts(houseId, list);
    }

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;

    /**
     * 长期合同占用覆盖：合同租期内显示「已出租」，同房源其余日期显示「空置」。
     *
     * <p>只影响展示，不写入日历表；短租预订时这些日期不可售。
     */
    private List<DayCellVO> overlayContracts(Long houseId, List<DayCellVO> list) {
        if (jdbc == null || list.isEmpty()) {
            return list;
        }
        LocalDate from = list.get(0).date();
        LocalDate to = list.get(list.size() - 1).date();
        java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                "select lease_start, lease_end, person_id from bp_biz_contract "
                        + "where house_id = ? and is_deleted = 0 "
                        + "and contract_status in ('SIGNING','EFFECTIVE','RENEWING') "
                        + "and lease_start <= ? and lease_end >= ?",
                houseId, to, from);
        if (rows.isEmpty()) {
            return list;
        }
        java.util.List<LocalDate[]> spans = new java.util.ArrayList<>();
        for (java.util.Map<String, Object> r : rows) {
            Object a = r.get("lease_start");
            Object b = r.get("lease_end");
            LocalDate s0 = a instanceof java.sql.Date d ? d.toLocalDate()
                    : (a == null ? null : LocalDate.parse(String.valueOf(a)));
            LocalDate e0 = b instanceof java.sql.Date d ? d.toLocalDate()
                    : (b == null ? null : LocalDate.parse(String.valueOf(b)));
            if (s0 != null && e0 != null) {
                spans.add(new LocalDate[]{s0, e0});
            }
        }
        List<DayCellVO> out = new java.util.ArrayList<>(list.size());
        for (DayCellVO c : list) {
            boolean leased = spans.stream().anyMatch(sp ->
                    !c.date().isBefore(sp[0]) && !c.date().isAfter(sp[1]));
            if (leased) {
                out.add(new DayCellVO(c.date(), "LEASED", "已出租", c.price(),
                        c.bookingId(), "CONTRACT", "长期合同占用"));
            } else {
                // 已有预订/维修等业务状态的日期不覆盖
                if ("AVAILABLE".equals(c.dayStatus())) {
                    out.add(new DayCellVO(c.date(), "VACANT", "空置", c.price(),
                            c.bookingId(), "CONTRACT", "合同区间外空置"));
                } else {
                    out.add(c);
                }
            }
        }
        return out;
    }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('日房态合同覆盖已加')

# ---------- 房源入住信息 ----------
p = os.path.join(BE, 'asset', 'controller', 'HouseController.java')
s = io.open(p, encoding='utf-8').read()
if 'occupancy' not in s:
    s = s.replace('''    @GetMapping("/{id}")''', '''    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbcTemplate;

    /**
     * 房源入住信息：当前合同、承租人、同住人与已入住人数。
     *
     * <p>已出租房源详情用，避免房东只看到房态看不到人。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:house:view")
    @GetMapping("/{id}/occupancy")
    public R<java.util.Map<String, Object>> occupancy(@PathVariable Long id) {
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        if (jdbcTemplate == null) {
            return R.ok(out);
        }
        java.util.List<java.util.Map<String, Object>> cs = jdbcTemplate.queryForList(
                "select c.id, c.contract_no, c.person_id, c.lease_start, c.lease_end, "
                        + "c.contract_status, p.person_name, p.phone from bp_biz_contract c "
                        + "left join bp_person p on p.id = c.person_id "
                        + "where c.house_id = ? and c.is_deleted = 0 "
                        + "and c.contract_status in ('SIGNING','EFFECTIVE','RENEWING') "
                        + "order by c.id desc limit 1", id);
        if (cs.isEmpty()) {
            out.put("occupied", false);
            out.put("tenantCount", 0);
            out.put("cohabitants", java.util.List.of());
            return R.ok(out);
        }
        java.util.Map<String, Object> c = cs.get(0);
        Object contractId = c.get("id");
        java.util.List<java.util.Map<String, Object>> co = jdbcTemplate.queryForList(
                "select co.name, co.relation, co.id_card_mask from bp_biz_contract_cohabitant co "
                        + "where co.contract_id = ? order by co.id", contractId);
        int tenantCount = 1 + co.size();
        out.put("occupied", true);
        out.put("contractId", contractId);
        out.put("contractNo", c.get("contract_no"));
        out.put("contractStatus", c.get("contract_status"));
        out.put("leaseStart", c.get("lease_start"));
        out.put("leaseEnd", c.get("lease_end"));
        out.put("tenantName", c.get("person_name"));
        out.put("tenantPhone", c.get("phone"));
        out.put("personId", c.get("person_id"));
        out.put("tenantCount", tenantCount);
        out.put("cohabitantCount", co.size());
        out.put("cohabitants", co);
        return R.ok(out);
    }

    @GetMapping("/{id}")''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('房源入住信息接口已加')
