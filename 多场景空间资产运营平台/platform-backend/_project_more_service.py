import io
p=r'src\main\java\com\yundao\platform\service\ProjectService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                        + "o.status, o.address, o.contact_name contactName, o.contact_phone contactPhone, o.remark, "''','''                        + "o.status, o.address, o.contact_name contactName, o.contact_phone contactPhone, o.remark, "
                        + "o.total_area totalArea, o.land_area landArea, o.property_type propertyType, o.build_year buildYear, "''')
s=s.replace('''                            + "address,contact_name,contact_phone,remark,"
                            + "org_path,sort_no,status,is_deleted) "
                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,?,?,?,?,0,'ENABLED',0)",
                    id, tenant, cmd.parentId(), cmd.orgCode().trim(), cmd.orgName().trim(),
                    cmd.sceneCode(), cmd.businessMode(), cmd.spaceTemplateId(),
                    cmd.defaultAssetTypeCode(), cmd.address(), cmd.contactName(), cmd.contactPhone(),
                    cmd.remark(), "/" + id + "/");''','''                            + "address,contact_name,contact_phone,remark,"
                            + "total_area,land_area,property_type,build_year,"
                            + "org_path,sort_no,status,is_deleted) "
                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,?,?,?,?,?,?,?,?,0,'ENABLED',0)",
                    id, tenant, cmd.parentId(), cmd.orgCode().trim(), cmd.orgName().trim(),
                    cmd.sceneCode(), cmd.businessMode(), cmd.spaceTemplateId(),
                    cmd.defaultAssetTypeCode(), cmd.address(), cmd.contactName(), cmd.contactPhone(),
                    cmd.remark(), cmd.totalArea(), cmd.landArea(), cmd.propertyType(), cmd.buildYear(),
                    "/" + id + "/");''')
s=s.replace('''                             String defaultAssetTypeCode, String address,
                             String contactName, String contactPhone, String remark) {
    }''','''                             String defaultAssetTypeCode, String address,
                             String contactName, String contactPhone, String remark,
                             java.math.BigDecimal totalArea, java.math.BigDecimal landArea,
                             String propertyType, Integer buildYear) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('project service more')
