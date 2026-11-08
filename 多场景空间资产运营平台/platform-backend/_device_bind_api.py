import io
p=r'src\main\java\com\yundao\platform\service\DeviceService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> bind(long deviceId, Long spaceId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select project_id projectId from bp_dev_device where id=? and tenant_id=? and is_deleted=0",
                deviceId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("设备不存在");
        }
        long projectId = ((Number) rows.get(0).get("projectId")).longValue();
        if (spaceId != null && count("select count(*) from bp_space where id=? and tenant_id=? and org_id=? and is_deleted=0",
                spaceId, tenant, projectId) == 0) {
            throw BizException.param("空间不属于设备所在项目");
        }
        jdbc.update("update bp_dev_device set space_id=?, update_time=now() where id=? and tenant_id=?",
                spaceId, deviceId, tenant);
        return Map.of("id", deviceId, "spaceId", spaceId == null ? "" : spaceId);
    }
'''
idx=s.rfind('    private long count(')
s=s[:idx]+insert+s[idx:]
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\DeviceController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping
    public R<Map<String, Object>> create''','''    @PostMapping("/{deviceId}/bind")
    public R<Map<String, Object>> bind(@org.springframework.web.bind.annotation.PathVariable long deviceId,
                                       @RequestBody Map<String, Long> body) {
        return R.ok(service.bind(deviceId, body.get("spaceId")));
    }

    @PostMapping
    public R<Map<String, Object>> create''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('device bind')
