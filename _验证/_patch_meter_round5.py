# -*- coding: utf-8 -*-
"""抄表：接口签名、控制器参数、批量出账、设备搜索。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


patch(os.path.join(BE, 'fin', 'service', 'MeterReadingService.java'), [
    ('''    PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId, Long feeItemId);''',
     '''    PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId, Long feeItemId);

    PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId, Long feeItemId,
                                    Long orgId, Boolean billed);''', '接口签名'),
])

p = os.path.join(BE, 'fin', 'controller', 'MeterReadingController.java')
s = io.open(p, encoding='utf-8').read()
if 'bill-batch' not in s:
    s = s.replace('''    public R<PageResult<FinMeterReading>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) Long feeItemId) {
        return R.ok(service.page(pageNum, pageSize, houseId, feeItemId));
    }''', '''    public R<PageResult<FinMeterReading>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) Long feeItemId,
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) Boolean billed) {
        return R.ok(service.page(pageNum, pageSize, houseId, feeItemId, orgId, billed));
    }

    /** 批量出账：逐条生成账单，返回成功/失败明细。 */
    @PostMapping("/bill-batch")
    @RequirePerm("fin:bill:create")
    public R<java.util.Map<String, Object>> billBatch(@RequestBody java.util.List<Long> ids) {
        int ok = 0;
        java.util.List<java.util.Map<String, Object>> errors = new java.util.ArrayList<>();
        for (Long id : ids) {
            try {
                service.bill(id);
                ok++;
            } catch (Exception e) {
                java.util.Map<String, Object> er = new java.util.LinkedHashMap<>();
                er.put("id", id);
                er.put("message", e.getMessage());
                errors.add(er);
            }
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("total", ids.size());
        out.put("billed", ok);
        out.put("failed", errors.size());
        out.put("errors", errors);
        return R.ok(out);
    }

    /** 按组织 + 设备名称/编号搜索计量设备（批量录入用）。 */
    @RequirePerm("fin:bill:view")
    @GetMapping("/devices-search")
    public R<java.util.List<java.util.Map<String, Object>>> devicesSearch(
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) String keyword) {
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        if (jdbc == null) {
            return R.ok(out);
        }
        StringBuilder sql = new StringBuilder(
                "select d.device_id, d.device_name, d.device_type, h.id as house_id, "
                        + "h.house_code, h.house_name, s.space_name, h.org_id, "
                        + "(select fi.id from bp_fin_fee_item fi where fi.calc_mode='METER' "
                        + "and (upper(fi.item_code) like concat('%', "
                        + "case d.device_type when 'ELEC_METER' then 'ELEC' "
                        + "when 'WATER_METER' then 'WATER' when 'GAS_METER' then 'GAS' "
                        + "when 'HEAT_METER' then 'HEAT' else 'X' end, '%')) limit 1) as fee_item_id "
                        + "from bp_dev_device d "
                        + "join bp_asset_house h on h.space_id = d.space_id "
                        + "left join bp_asset_space s on s.id = d.space_id "
                        + "where d.device_type in ('ELEC_METER','WATER_METER','GAS_METER','HEAT_METER') ");
        java.util.List<Object> args = new java.util.ArrayList<>();
        if (orgId != null) {
            sql.append("and h.org_id = ? ");
            args.add(orgId);
        }
        if (keyword != null && !keyword.isBlank()) {
            sql.append("and (d.device_id like concat('%', ?, '%') "
                    + "or d.device_name like concat('%', ?, '%')) ");
            args.add(keyword);
            args.add(keyword);
        }
        sql.append("order by d.device_id limit 100");
        out.addAll(jdbc.queryForList(sql.toString(), args.toArray()));
        return R.ok(out);
    }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('抄表控制器已扩展')
