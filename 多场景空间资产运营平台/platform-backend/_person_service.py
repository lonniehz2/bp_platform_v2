import io
p=r'src\main\java\com\yundao\platform\service\PersonService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                "select id, person_code personCode, person_name personName, phone, "
                        + "id_card_mask idCardMask, person_type personType, verify_status verifyStatus, status "''','''                "select id, person_code personCode, person_name personName, phone, "
                        + "id_card_mask idCardMask, person_type personType, verify_status verifyStatus, status, "
                        + "gender, birth_date birthDate, address, employer, emergency_contact emergencyContact, remark "''')
s=s.replace('''            jdbc.update("insert into bp_person(id,tenant_id,person_code,person_name,phone,"
                            + "id_card_mask,person_type,status,is_deleted) values(?,?,?,?,?,?,?,'ENABLED',0)",
                    id, tenant, cmd.personCode().trim(), cmd.personName().trim(), cmd.phone(),
                    cmd.idCardMask(), cmd.personType());''','''            jdbc.update("insert into bp_person(id,tenant_id,person_code,person_name,phone,"
                            + "id_card_mask,person_type,gender,birth_date,address,employer,emergency_contact,remark,"
                            + "status,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?,?,'ENABLED',0)",
                    id, tenant, cmd.personCode().trim(), cmd.personName().trim(), cmd.phone(),
                    cmd.idCardMask(), cmd.personType(), cmd.gender(), cmd.birthDate(), cmd.address(),
                    cmd.employer(), cmd.emergencyContact(), cmd.remark());''')
s=s.replace('''    public record PersonCmd(String personCode, String personName, String phone,
                            String idCardMask, String personType) {
    }''','''    public record PersonCmd(String personCode, String personName, String phone,
                            String idCardMask, String personType, String gender,
                            LocalDate birthDate, String address, String employer,
                            String emergencyContact, String remark) {
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('person service')
