package com.yundao.bp.person.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 实名认证流水。对应 `bp_person_verify_record`。
 */
@Data
@TableName("bp_person_verify_record")
public class PersonVerifyRecord {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long personId;
    /** PERSONAL / ORG / FACE_COMPARE / IDCARD_DECODE */
    private String verifyType;
    /** 提交的姓名（加密存储） */
    private String userName;
    /** 身份证哈希（可判等，不可反推） */
    private String idCardHash;
    private String faceImgUrl;
    private String idcardImgUrl;
    private String requestNo;
    private String commandId;
    private String responseCode;
    private String resultCode;
    private BigDecimal faceScore;
    /** 0 null / 1 同一人 / 2 不同人 / 3 不能确定 / 4 无法比对 / 5 库中无照片 */
    private String faceResult;
    /** 1 一致 / 2 不一致 / 3 库中无此号 */
    private String citizenResult;
    private Integer verifyPass;
    private String failReason;
    private String rawResponse;
    private LocalDateTime createTime;

    // ---------- 非持久化：列表展示用（办理人员要能看出是谁） ----------
    @TableField(exist = false)
    private String personName;
    @TableField(exist = false)
    private String phoneMask;
    @TableField(exist = false)
    private String idCardMask;
}
