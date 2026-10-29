# -*- coding: utf-8 -*-
import io

# IamTenant 字段 + 访问器
p = r'..\backend\src\main\java\com\yundao\bp\iam\entity\IamTenant.java'
s = io.open(p, encoding='utf-8').read()
if 'contactName' not in s:
    s = s.replace('    private String regionCode;', '''    private String regionCode;
    private String contactName;
    private String contactPhone;
    private String businessTypeCode;
    private Integer deleted;
    private LocalDateTime archiveTime;''', 1)
    accessors = '''
    public String getContactName() { return contactName; }

    public void setContactName(String contactName) { this.contactName = contactName; }

    public String getContactPhone() { return contactPhone; }

    public void setContactPhone(String contactPhone) { this.contactPhone = contactPhone; }

    public String getBusinessTypeCode() { return businessTypeCode; }

    public void setBusinessTypeCode(String businessTypeCode) {
        this.businessTypeCode = businessTypeCode;
    }

    public Integer getDeleted() { return deleted; }

    public void setDeleted(Integer deleted) { this.deleted = deleted; }

    public LocalDateTime getArchiveTime() { return archiveTime; }

    public void setArchiveTime(LocalDateTime archiveTime) { this.archiveTime = archiveTime; }
'''
    idx = s.rfind('}')
    s = s[:idx] + accessors + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('IamTenant updated')

# IamUser 字段（Lombok）
p = r'..\backend\src\main\java\com\yundao\bp\iam\entity\IamUser.java'
s = io.open(p, encoding='utf-8').read()
if 'mustChangePassword' not in s:
    s = s.replace('    private String status;', '''    private String status;
    /** 首次登录/重置后需改密 */
    private Integer mustChangePassword;
    private Integer failCount;
    private LocalDateTime lockedUntil;''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('IamUser updated')
