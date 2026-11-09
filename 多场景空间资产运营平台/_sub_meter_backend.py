import io
p=r'platform-backend\src\main\java\com\yundao\platform\service\GuaranteeSubsidyService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> update(long subsidyId, SubsidyCmd cmd) {
        if (cmd.amount() == null || cmd.amount().signum() < 0) throw BizException.param("补贴金额不能为负数");
        if (cmd.startDate() == null || cmd.endDate() == null || cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.param("补贴起止日期不合法");
        }
        int updated = jdbc.update("update guarantee_subsidy set subsidy_type=?, subsidy_amount=?, start_date=?, "
                        + "end_date=?, remark=?, update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.subsidyType() == null ? "RENT_SUBSIDY" : cmd.subsidyType(), cmd.amount(),
                cmd.startDate(), cmd.endDate(), cmd.remark(), subsidyId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("补贴不存在");
        return Map.of("id", subsidyId, "subsidyAmount", cmd.amount());
    }

    public Map<String, Object> terminate(long subsidyId) {
        int updated = jdbc.update("update guarantee_subsidy set subsidy_status='TERMINATED', update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0", subsidyId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("补贴不存在");
        return Map.of("id", subsidyId, "subsidyStatus", "TERMINATED");
    }

'''
marker='''    public record SubsidyCmd('''
if marker not in s: raise SystemExit('marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'platform-backend\src\main\java\com\yundao\platform\controller\GuaranteeSubsidyController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/contracts/{contractId}/subsidies")''','''    @PostMapping("/subsidies/{subsidyId}/update")
    public R<Map<String, Object>> update(@PathVariable long subsidyId,
                                         @RequestBody GuaranteeSubsidyService.SubsidyCmd cmd) {
        return R.ok(service.update(subsidyId, cmd));
    }

    @PostMapping("/subsidies/{subsidyId}/terminate")
    public R<Map<String, Object>> terminate(@PathVariable long subsidyId) {
        return R.ok(service.terminate(subsidyId));
    }

    @PostMapping("/contracts/{contractId}/subsidies")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
# meter service update/status
p=r'platform-backend\src\main\java\com\yundao\platform\service\MeterService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> update(long meterId, MeterCmd cmd) {
        if (cmd.meterNo() == null || cmd.meterNo().isBlank()) throw BizException.param("表号不能为空");
        int updated = jdbc.update("update guarantee_meter set house_id=?, meter_type=?, meter_no=?, "
                        + "install_date=?, update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.houseId(), cmd.meterType(), cmd.meterNo().trim(), cmd.installDate(),
                meterId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("表计不存在");
        return Map.of("id", meterId, "meterNo", cmd.meterNo());
    }

    public Map<String, Object> setStatus(long meterId, String status) {
        if (!List.of("ACTIVE", "DISABLED").contains(status)) throw BizException.param("状态不合法");
        int updated = jdbc.update("update guarantee_meter set meter_status=?, update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0", status, meterId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("表计不存在");
        return Map.of("id", meterId, "meterStatus", status);
    }

'''
marker='''    public List<Map<String, Object>> readings(long meterId) {'''
if marker not in s: raise SystemExit('meter marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'platform-backend\src\main\java\com\yundao\platform\controller\MeterController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @GetMapping("/{meterId}/readings")''','''    @PostMapping("/{meterId}/update")
    public R<Map<String, Object>> update(@PathVariable long meterId,
                                         @RequestBody MeterService.MeterCmd cmd) {
        return R.ok(service.update(meterId, cmd));
    }

    @PostMapping("/{meterId}/status")
    public R<Map<String, Object>> status(@PathVariable long meterId,
                                         @RequestBody Map<String, String> body) {
        return R.ok(service.setStatus(meterId, body.get("status")));
    }

    @GetMapping("/{meterId}/readings")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('backend subsidy/meter')
