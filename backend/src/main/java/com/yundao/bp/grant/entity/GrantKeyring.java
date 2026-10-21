package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 钥匙包（人员名下多介质钥匙）。对应 `bp_grant_keyring`。
 */
@Data
@TableName("bp_grant_keyring")
public class GrantKeyring {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long personId;
    /** FACE / FINGERPRINT / PALM_VEIN / PASSWORD / CARD / IDCARD / QRCODE */
    private String keyType;
    /** 四分类：PERSONAL_REAL / PERSONAL_UNREAL / ORG_REAL / ORG_UNREAL */
    private String keyClass;
    private String keyAlias;
    /** 介质模块类型：00 蓝牙 / 01 键盘 / 02 刷卡 / 04 指纹 / 05 掌静脉 / 06 人脸 */
    private String channelModuleType;
    /** 介质类型编码（IoT §8.3.4） */
    private String channelType;
    /** 介质值（加密存储） */
    private String channelValue;
    private String channelValue2;
    /** SELF_APP / ADMIN / IDCARD / IMPORT */
    private String keySource;
    /** FACE_VERIFY / ORG_VERIFY / NONE */
    private String verifyWay;
    /** 是否实名介质（1 强安全） */
    private Integer isReal;
    /** ALL_GRANTED / SPECIFIC */
    private String syncScope;
    /** ACTIVE / FROZEN / DELETED / EXPIRED */
    private String keyStatus;
    private LocalDateTime expireTime;
    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
