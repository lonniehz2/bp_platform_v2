import io
p=r'src\main\java\com\yundao\platform\service\HouseService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''        int updated = jdbc.update("update bp_house set area=coalesce(?,area), inner_area=coalesce(?,inner_area), "
                        + "house_status=coalesce(?,house_status), asset_type_code=coalesce(?,asset_type_code), "
                        + "update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.area(), cmd.innerArea(), cmd.houseStatus(), cmd.assetTypeCode(), houseId, TenantContext.require());''','''        int updated = jdbc.update("update bp_house set area=coalesce(?,area), inner_area=coalesce(?,inner_area), "
                        + "house_status=coalesce(?,house_status), asset_type_code=coalesce(?,asset_type_code), "
                        + "layout_type=coalesce(?,layout_type), orientation=coalesce(?,orientation), "
                        + "floor_no=coalesce(?,floor_no), total_floors=coalesce(?,total_floors), "
                        + "update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.area(), cmd.innerArea(), cmd.houseStatus(), cmd.assetTypeCode(),
                cmd.layoutType(), cmd.orientation(), cmd.floorNo(), cmd.totalFloors(),
                houseId, TenantContext.require());''')
s=s.replace('''    public record HouseUpdate(java.math.BigDecimal area, java.math.BigDecimal innerArea,
                              String houseStatus, String assetTypeCode) {
    }''','''    public record HouseUpdate(java.math.BigDecimal area, java.math.BigDecimal innerArea,
                              String houseStatus, String assetTypeCode, String layoutType,
                              String orientation, Integer floorNo, Integer totalFloors) {
    }''')
s=s.replace('''                        + "asset_type_code assetTypeCode, area, inner_area innerArea, house_status houseStatus "''','''                        + "asset_type_code assetTypeCode, area, inner_area innerArea, house_status houseStatus, "
                        + "layout_type layoutType, orientation, floor_no floorNo, total_floors totalFloors "''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('house service')
