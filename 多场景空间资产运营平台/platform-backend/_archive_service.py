import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeApplicationService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                        + "a.housing_status housingStatus, a.urgency, a.remark, "''','''                        + "a.housing_status housingStatus, a.urgency, a.remark, "
                        + "a.guarantee_type guaranteeType, a.family_type familyType, "
                        + "a.subsidy_status subsidyStatus, a.archive_no archiveNo, "''')
s=s.replace('''                            + "applicant_person_id,application_type,family_size,contact_phone,income_level,"
                            + "housing_status,urgency,remark,application_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?,?, 'DRAFT',0)",
                    id, tenant, cmd.projectId(), cmd.applicationNo().trim(), cmd.applicantPersonId(),
                    cmd.applicationType() == null ? "PUBLIC_RENTAL" : cmd.applicationType(), familySize,
                    cmd.contactPhone(), cmd.incomeLevel(), cmd.housingStatus(), cmd.urgency(), cmd.remark());''','''                            + "applicant_person_id,application_type,family_size,contact_phone,income_level,"
                            + "housing_status,urgency,remark,guarantee_type,family_type,subsidy_status,archive_no,"
                            + "application_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'DRAFT',0)",
                    id, tenant, cmd.projectId(), cmd.applicationNo().trim(), cmd.applicantPersonId(),
                    cmd.applicationType() == null ? "PUBLIC_RENTAL" : cmd.applicationType(), familySize,
                    cmd.contactPhone(), cmd.incomeLevel(), cmd.housingStatus(), cmd.urgency(), cmd.remark(),
                    cmd.guaranteeType(), cmd.familyType(), cmd.subsidyStatus(), cmd.archiveNo());''')
s=s.replace('''                                 String incomeLevel, String housingStatus, String urgency, String remark) {
    }''','''                                 String incomeLevel, String housingStatus, String urgency, String remark,
                                 String guaranteeType, String familyType, String subsidyStatus, String archiveNo) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('archive service')
