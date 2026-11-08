import io
p=r'src\main\java\com\yundao\platform\service\DeviceService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> repair(long deviceId, String reason) {
        String tenant = TenantContext.require();
        int updated = jdbc.update("update bp_dev_device set business_status='FAULT', "
                + "remark=concat(coalesce(remark,''), ?), update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0",
                "\\n报修:" + (reason == null ? "" : reason), deviceId, tenant);
        if (updated == 0) throw BizException.notFound("设备不存在");
        return Map.of("id", deviceId, "businessStatus", "FAULT");
    }

    public Map<String, Object> enable(long deviceId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select business_status businessStatus from bp_dev_device "
                        + "where id=? and tenant_id=? and is_deleted=0", deviceId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("设备不存在");
        String status = String.valueOf(rows.get(0).get("businessStatus"));
        if (!"FAULT".equals(status) && !"DISABLED".equals(status)) {
            throw BizException.conflict("只有故障或停用设备可以启用");
        }
        jdbc.update("update bp_dev_device set business_status='IN_USE', update_time=now() "
                + "where id=? and tenant_id=?", deviceId, tenant);
        return Map.of("id", deviceId, "businessStatus", "IN_USE");
    }

'''
marker='''    private long count(String sql, Object... args) {'''
if marker not in s: raise SystemExit('marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\DeviceController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping
    public R<Map<String, Object>> create''','''    @PostMapping("/{deviceId}/repair")
    public R<Map<String, Object>> repair(@org.springframework.web.bind.annotation.PathVariable long deviceId,
                                         @RequestBody(required = false) Map<String, String> body) {
        permissions.require("device:repair");
        return R.ok(service.repair(deviceId, body == null ? null : body.get("reason")));
    }

    @PostMapping("/{deviceId}/enable")
    public R<Map<String, Object>> enable(@org.springframework.web.bind.annotation.PathVariable long deviceId) {
        permissions.require("device:enable");
        return R.ok(service.enable(deviceId));
    }

    @PostMapping
    public R<Map<String, Object>> create''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('device lifecycle')
