package com.yundao.bp.person.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 人员主档。对应表 {@code bp_person}。
 *
 * <p>⚠️ <b>敏感字段三列</b>：{@code id_card}（密文）/ {@code id_card_hash}（检索）/
 * {@code id_card_mask}（展示）。手机号同理。见 {@link com.yundao.bp.person.util.SensitiveDataCodec}。
 */
@TableName("bp_person")
public class Person {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String personCode;
    private String personName;
    private String realName;

    /** 手机号（密文） */
    private String phone;
    private String phoneHash;

    /** 身份证号（密文） */
    private String idCard;
    private String idCardHash;
    private String idCardMask;

    /** M / F / U */
    private String gender;
    private LocalDate birthday;
    private String nation;
    private String nativePlace;

    /** URBAN 城镇 / RURAL 农村 / OTHER */
    private String householdType;
    private String householdAddr;

    /** SINGLE / MARRIED / DIVORCED / WIDOWED */
    private String maritalStatus;
    private String education;
    private String title;
    private String employer;
    private String healthStatus;

    /** SELF / ADMIN / IMPORT / HR_SYNC / GOV_SYNC */
    private String personSource;
    private Long orgId;

    /** UNVERIFIED / VERIFIED / FAILED / EXPIRED */
    private String verifyStatus;
    private LocalDateTime verifyTime;
    /** PERSONAL / ORG / NONE */
    private String verifyLevel;

    private String bindDeviceId;
    private String bindIdCardHash;

    /** NORMAL / BLACKLIST / CANCELLED */
    private String personStatus;
    private String avatarUrl;
    private Integer privacyFlag;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTenantId() { return tenantId; }
    public void setTenantId(String tenantId) { this.tenantId = tenantId; }
    public String getPersonCode() { return personCode; }
    public void setPersonCode(String personCode) { this.personCode = personCode; }
    public String getPersonName() { return personName; }
    public void setPersonName(String personName) { this.personName = personName; }
    public String getRealName() { return realName; }
    public void setRealName(String realName) { this.realName = realName; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getPhoneHash() { return phoneHash; }
    public void setPhoneHash(String phoneHash) { this.phoneHash = phoneHash; }
    public String getIdCard() { return idCard; }
    public void setIdCard(String idCard) { this.idCard = idCard; }
    public String getIdCardHash() { return idCardHash; }
    public void setIdCardHash(String idCardHash) { this.idCardHash = idCardHash; }
    public String getIdCardMask() { return idCardMask; }
    public void setIdCardMask(String idCardMask) { this.idCardMask = idCardMask; }
    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }
    public LocalDate getBirthday() { return birthday; }
    public void setBirthday(LocalDate birthday) { this.birthday = birthday; }
    public String getNation() { return nation; }
    public void setNation(String nation) { this.nation = nation; }
    public String getNativePlace() { return nativePlace; }
    public void setNativePlace(String nativePlace) { this.nativePlace = nativePlace; }
    public String getHouseholdType() { return householdType; }
    public void setHouseholdType(String householdType) { this.householdType = householdType; }
    public String getHouseholdAddr() { return householdAddr; }
    public void setHouseholdAddr(String householdAddr) { this.householdAddr = householdAddr; }
    public String getMaritalStatus() { return maritalStatus; }
    public void setMaritalStatus(String maritalStatus) { this.maritalStatus = maritalStatus; }
    public String getEducation() { return education; }
    public void setEducation(String education) { this.education = education; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getEmployer() { return employer; }
    public void setEmployer(String employer) { this.employer = employer; }
    public String getHealthStatus() { return healthStatus; }
    public void setHealthStatus(String healthStatus) { this.healthStatus = healthStatus; }
    public String getPersonSource() { return personSource; }
    public void setPersonSource(String personSource) { this.personSource = personSource; }
    public Long getOrgId() { return orgId; }
    public void setOrgId(Long orgId) { this.orgId = orgId; }
    public String getVerifyStatus() { return verifyStatus; }
    public void setVerifyStatus(String verifyStatus) { this.verifyStatus = verifyStatus; }
    public LocalDateTime getVerifyTime() { return verifyTime; }
    public void setVerifyTime(LocalDateTime verifyTime) { this.verifyTime = verifyTime; }
    public String getVerifyLevel() { return verifyLevel; }
    public void setVerifyLevel(String verifyLevel) { this.verifyLevel = verifyLevel; }
    public String getBindDeviceId() { return bindDeviceId; }
    public void setBindDeviceId(String bindDeviceId) { this.bindDeviceId = bindDeviceId; }
    public String getBindIdCardHash() { return bindIdCardHash; }
    public void setBindIdCardHash(String bindIdCardHash) { this.bindIdCardHash = bindIdCardHash; }
    public String getPersonStatus() { return personStatus; }
    public void setPersonStatus(String personStatus) { this.personStatus = personStatus; }
    public String getAvatarUrl() { return avatarUrl; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }
    public Integer getPrivacyFlag() { return privacyFlag; }
    public void setPrivacyFlag(Integer privacyFlag) { this.privacyFlag = privacyFlag; }
    public String getRemark() { return remark; }
    public void setRemark(String remark) { this.remark = remark; }
    public Integer getIsDeleted() { return isDeleted; }
    public void setIsDeleted(Integer isDeleted) { this.isDeleted = isDeleted; }
    public String getCreateBy() { return createBy; }
    public void setCreateBy(String createBy) { this.createBy = createBy; }
    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
    public String getUpdateBy() { return updateBy; }
    public void setUpdateBy(String updateBy) { this.updateBy = updateBy; }
    public LocalDateTime getUpdateTime() { return updateTime; }
    public void setUpdateTime(LocalDateTime updateTime) { this.updateTime = updateTime; }
}
