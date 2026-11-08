import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeApplicationService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                        + "a.application_type applicationType, a.family_size familySize, "''','''                        + "a.application_type applicationType, a.family_size familySize, "
                        + "a.contact_phone contactPhone, a.income_level incomeLevel, "
                        + "a.housing_status housingStatus, a.urgency, a.remark, "''')
s=s.replace('''            jdbc.update("insert into guarantee_application(id,tenant_id,project_id,application_no,"
                            + "applicant_person_id,application_type,family_size,application_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?, 'DRAFT',0)",
                    id, tenant, cmd.projectId(), cmd.applicationNo().trim(), cmd.applicantPersonId(),
                    cmd.applicationType() == null ? "PUBLIC_RENTAL" : cmd.applicationType(), familySize);''','''            jdbc.update("insert into guarantee_application(id,tenant_id,project_id,application_no,"
                            + "applicant_person_id,application_type,family_size,contact_phone,income_level,"
                            + "housing_status,urgency,remark,application_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?,?, 'DRAFT',0)",
                    id, tenant, cmd.projectId(), cmd.applicationNo().trim(), cmd.applicantPersonId(),
                    cmd.applicationType() == null ? "PUBLIC_RENTAL" : cmd.applicationType(), familySize,
                    cmd.contactPhone(), cmd.incomeLevel(), cmd.housingStatus(), cmd.urgency(), cmd.remark());''')
s=s.replace('''    public record ApplicationCmd(long projectId, String applicationNo, Long applicantPersonId,
                                 String applicationType, Integer familySize) {
    }''','''    public record ApplicationCmd(long projectId, String applicationNo, Long applicantPersonId,
                                 String applicationType, Integer familySize, String contactPhone,
                                 String incomeLevel, String housingStatus, String urgency, String remark) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('application service')
