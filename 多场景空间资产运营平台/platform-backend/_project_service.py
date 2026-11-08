import io
p=r'src\main\java\com\yundao\platform\service\ProjectService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                        + "o.status, o.create_time createTime, "''','''                        + "o.status, o.address, o.contact_name contactName, o.contact_phone contactPhone, o.remark, "
                        + "o.create_time createTime, "''')
s=s.replace('''                            + "scene_code,business_mode,space_template_id,default_asset_type_code,"
                            + "org_path,sort_no,status,is_deleted) "
                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,0,'ENABLED',0)",
                    id, tenant, cmd.parentId(), cmd.orgCode().trim(), cmd.orgName().trim(),
                    cmd.sceneCode(), cmd.businessMode(), cmd.spaceTemplateId(),
                    cmd.defaultAssetTypeCode(), "/" + id + "/");''','''                            + "scene_code,business_mode,space_template_id,default_asset_type_code,"
                            + "address,contact_name,contact_phone,remark,"
                            + "org_path,sort_no,status,is_deleted) "
                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,?,?,?,0,'ENABLED',0)",
                    id, tenant, cmd.parentId(), cmd.orgCode().trim(), cmd.orgName().trim(),
                    cmd.sceneCode(), cmd.businessMode(), cmd.spaceTemplateId(),
                    cmd.defaultAssetTypeCode(), cmd.address(), cmd.contactName(), cmd.contactPhone(),
                    cmd.remark(), "/" + id + "/");''')
s=s.replace('''    public record ProjectCmd(String orgCode, String orgName, Long parentId, String sceneCode,
                             String businessMode, Long spaceTemplateId,
                             String defaultAssetTypeCode) {
    }''','''    public record ProjectCmd(String orgCode, String orgName, Long parentId, String sceneCode,
                             String businessMode, Long spaceTemplateId,
                             String defaultAssetTypeCode, String address,
                             String contactName, String contactPhone, String remark) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('project service')
