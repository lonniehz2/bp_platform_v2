# -*- coding: utf-8 -*-
"""生成钥匙包 + 授权对账 + IoT 人员映射：实体 + Mapper + 常量"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def ent(name, table, fields, doc, logic=False):
    li = 'import com.baomidou.mybatisplus.annotation.TableLogic;\n' if logic else ''
    lg = '\n    @TableLogic\n    private Integer isDeleted;\n' if logic else ''
    return f'''package com.yundao.bp.grant.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
{li}import java.time.LocalDateTime;
import lombok.Data;

/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{chr(10).join(fields)}
{lg}}}
'''


F['grant/entity/GrantKeyring.java'] = ent('GrantKeyring', 'bp_grant_keyring', [
    '    private String tenantId;',
    '    private Long personId;',
    '    /** FACE / FINGERPRINT / PALM_VEIN / PASSWORD / CARD / IDCARD / QRCODE */',
    '    private String keyType;',
    '    /** 四分类：PERSONAL_REAL / PERSONAL_UNREAL / ORG_REAL / ORG_UNREAL */',
    '    private String keyClass;',
    '    private String keyAlias;',
    '    /** 介质模块类型：00 蓝牙 / 01 键盘 / 02 刷卡 / 04 指纹 / 05 掌静脉 / 06 人脸 */',
    '    private String channelModuleType;',
    '    /** 介质类型编码（IoT §8.3.4） */',
    '    private String channelType;',
    '    /** 介质值（加密存储） */',
    '    private String channelValue;',
    '    private String channelValue2;',
    '    /** SELF_APP / ADMIN / IDCARD / IMPORT */',
    '    private String keySource;',
    '    /** FACE_VERIFY / ORG_VERIFY / NONE */',
    '    private String verifyWay;',
    '    /** 是否实名介质（1 强安全） */',
    '    private Integer isReal;',
    '    /** ALL_GRANTED / SPECIFIC */',
    '    private String syncScope;',
    '    /** ACTIVE / FROZEN / DELETED / EXPIRED */',
    '    private String keyStatus;',
    '    private LocalDateTime expireTime;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], '钥匙包（人员名下多介质钥匙）。对应 `bp_grant_keyring`。', True)

F['grant/entity/GrantReconcileDiff.java'] = ent('GrantReconcileDiff',
                                                'bp_grant_reconcile_diff', [
    '    private String tenantId;',
    '    private String deviceId;',
    '    private String lockId;',
    '    private Long personId;',
    '    /** IoT 侧授权对象账号（手机号） */',
    '    private String targetUserMobile;',
    '    /** LOCAL_MISSING / IOT_EXTRA / PERIOD_MISMATCH / VALUE_MISMATCH */',
    '    private String diffType;',
    '    private String localValue;',
    '    private String iotValue;',
    '    /** REGRANT / REVOKE / MANUAL / IGNORED */',
    '    private String handleAction;',
    '    /** PENDING / HANDLED / IGNORED */',
    '    private String handleStatus;',
    '    private LocalDateTime handleTime;',
    '    private String handleRemark;',
    '    private LocalDateTime createTime;',
], '授权对账差异。对应 `bp_grant_reconcile_diff`。')

F['grant/entity/GrantIotPersonMap.java'] = ent('GrantIotPersonMap',
                                               'bp_grant_iot_person_map', [
    '    private String tenantId;',
    '    private Long personId;',
    '    /** IoT 人员主键 ownerId */',
    '    private String iotOwnerId;',
    '    private String iotOrganId;',
    '    /** IoT 侧人员账号（手机号） */',
    '    private String iotAccount;',
    '    /** SYNCED / PENDING / FAILED */',
    '    private String syncStatus;',
    '    private LocalDateTime syncTime;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], '本地人员与 IoT 人员的映射。对应 `bp_grant_iot_person_map`。')

for n in ('GrantKeyring', 'GrantReconcileDiff', 'GrantIotPersonMap'):
    F['grant/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.grant.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.grant.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== 常量 ====================
F['grant/constant/KeyType.java'] = '''package com.yundao.bp.grant.constant;

/**
 * 钥匙类型。
 *
 * <p>{@code code} 对应 IoT 介质模块类型与介质类型编码，
 * 便于下发时直接映射，不在业务层写 if/else。
 */
public enum KeyType {

    FACE("人脸", "06", "601"),
    FINGERPRINT("指纹", "04", "401"),
    PALM_VEIN("掌静脉", "05", "501"),
    PASSWORD("密码", "01", "101"),
    CARD("卡片", "02", "201"),
    IDCARD("身份证", "02", "202"),
    QRCODE("二维码", "07", "701");

    private final String label;
    private final String moduleType;
    private final String channelType;

    KeyType(String label, String moduleType, String channelType) {
        this.label = label;
        this.moduleType = moduleType;
        this.channelType = channelType;
    }

    public String label() {
        return label;
    }

    public String moduleType() {
        return moduleType;
    }

    public String channelType() {
        return channelType;
    }

    public static KeyType of(String code) {
        for (KeyType t : values()) {
            if (t.name().equals(code)) {
                return t;
            }
        }
        return null;
    }
}
'''

F['grant/constant/KeyClass.java'] = '''package com.yundao.bp.grant.constant;

/**
 * 钥匙四分类（★ 级「四级权限」考核要求）。
 *
 * <p>按「是否实名」×「个人/组织」两个维度切分，决定介质的安全等级与审批要求：
 *
 * <table border="1">
 *   <tr><th></th><th>实名</th><th>非实名</th></tr>
 *   <tr><th>个人</th><td>PERSONAL_REAL</td><td>PERSONAL_UNREAL</td></tr>
 *   <tr><th>组织</th><td>ORG_REAL</td><td>ORG_UNREAL</td></tr>
 * </table>
 *
 * <p><b>实名介质</b>（人脸/指纹/身份证）属强安全，可用于开大门与户门；
 * <b>非实名介质</b>（密码/临时卡）属弱安全，只能开门锁且应限期有效。
 */
public enum KeyClass {

    PERSONAL_REAL("个人实名", true, false),
    PERSONAL_UNREAL("个人非实名", false, false),
    ORG_REAL("组织实名", true, true),
    ORG_UNREAL("组织非实名", false, true);

    private final String label;
    private final boolean realName;
    private final boolean orgOwned;

    KeyClass(String label, boolean realName, boolean orgOwned) {
        this.label = label;
        this.realName = realName;
        this.orgOwned = orgOwned;
    }

    public String label() {
        return label;
    }

    public boolean realName() {
        return realName;
    }

    public boolean orgOwned() {
        return orgOwned;
    }

    /** 是否允许开门禁大门（只有实名介质允许）。 */
    public boolean allowMainDoor() {
        return realName;
    }

    /** 是否必须设置有效期（弱安全介质必须限期）。 */
    public boolean requireExpireTime() {
        return !realName;
    }

    /**
     * 按钥匙类型与来源推导默认分类。
     *
     * <p>规则：实名核验过的为人实名；身份证下发的属个人实名；
     * 后台录入的密码/临时卡属个人非实名；组织统一发放的卡片属组织分类。
     */
    public static KeyClass derive(KeyType type, String verifyWay, String keySource) {
        boolean verified = "FACE_VERIFY".equals(verifyWay) || "ORG_VERIFY".equals(verifyWay);
        boolean idcard = type == KeyType.IDCARD || "IDCARD".equals(keySource);
        boolean strongType = type == KeyType.FACE || type == KeyType.FINGERPRINT
                || type == KeyType.PALM_VEIN;
        boolean real = verified || idcard || strongType;
        boolean org = "ORG_VERIFY".equals(verifyWay);
        if (org) {
            return real ? ORG_REAL : ORG_UNREAL;
        }
        return real ? PERSONAL_REAL : PERSONAL_UNREAL;
    }

    public static KeyClass of(String code) {
        for (KeyClass c : values()) {
            if (c.name().equals(code)) {
                return c;
            }
        }
        return null;
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
