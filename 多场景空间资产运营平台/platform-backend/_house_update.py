import io
p=r'src\main\java\com\yundao\platform\service\HouseService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''import com.yundao.platform.common.tenant.TenantContext;''','''import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;''')
s=s.replace('''    public List<Map<String, Object>> list(long projectId) {''','''    public Map<String, Object> update(long houseId, HouseUpdate cmd) {
        if (cmd.houseStatus() != null && !List.of("VACANT", "ALLOCATED", "OCCUPIED", "FROZEN").contains(cmd.houseStatus())) {
            throw BizException.param("房态不合法");
        }
        int updated = jdbc.update("update bp_house set area=coalesce(?,area), inner_area=coalesce(?,inner_area), "
                        + "house_status=coalesce(?,house_status), asset_type_code=coalesce(?,asset_type_code), "
                        + "update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.area(), cmd.innerArea(), cmd.houseStatus(), cmd.assetTypeCode(), houseId, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("房源不存在");
        }
        return Map.of("id", houseId, "houseStatus", cmd.houseStatus() == null ? "UNCHANGED" : cmd.houseStatus());
    }

    public record HouseUpdate(java.math.BigDecimal area, java.math.BigDecimal innerArea,
                              String houseStatus, String assetTypeCode) {
    }

    public List<Map<String, Object>> list(long projectId) {''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\HouseController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @GetMapping''','''    @org.springframework.web.bind.annotation.PostMapping("/{houseId}/update")
    public R<Map<String, Object>> update(@org.springframework.web.bind.annotation.PathVariable long houseId,
                                         @org.springframework.web.bind.annotation.RequestBody HouseService.HouseUpdate cmd) {
        return R.ok(service.update(houseId, cmd));
    }

    @GetMapping''',1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('house update')
