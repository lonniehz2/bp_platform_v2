# -*- coding: utf-8 -*-
"""修正 KeyClass.derive：ORG_VERIFY 只决定归属，实名由类型/人证核验/身份证决定"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\grant\constant\KeyClass.java')
s = io.open(P, encoding='utf-8').read()

old = '''    public static KeyClass derive(KeyType type, String verifyWay, String keySource) {
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
    }'''

new = '''    public static KeyClass derive(KeyType type, String verifyWay, String keySource) {
        // 实名性：只有「做过人证核验」「身份证下发」「生物特征类型」才算实名。
        // 注意：ORG_VERIFY 只表示由组织核验并担保归属，不单独构成实名依据，
        // 否则 ORG_UNREAL 永远取不到（四分类会退化成三类）。
        boolean faceVerified = "FACE_VERIFY".equals(verifyWay);
        boolean idcard = type == KeyType.IDCARD || "IDCARD".equals(keySource);
        boolean strongType = type == KeyType.FACE || type == KeyType.FINGERPRINT
                || type == KeyType.PALM_VEIN;
        boolean real = faceVerified || idcard || strongType;

        // 归属：ORG_VERIFY 表示该钥匙由组织持有/担保（如单位集体租赁），
        // 否则归个人。
        boolean org = "ORG_VERIFY".equals(verifyWay);
        if (org) {
            return real ? ORG_REAL : ORG_UNREAL;
        }
        return real ? PERSONAL_REAL : PERSONAL_UNREAL;
    }'''

assert old in s, '锚点缺失'
s = s.replace(old, new, 1)

# 同步补一个可达性说明到枚举文档
s = s.replace(''' * <p><b>实名介质</b>（人脸/指纹/身份证）属强安全，可用于开大门与户门；
 * <b>非实名介质</b>（密码/临时卡）属弱安全，只能开门锁且应限期有效。''',
              ''' * <p><b>实名介质</b>（人脸/指纹/掌静脉/身份证/人证核验通过）属强安全，
 * 可用于开大门与户门；<b>非实名介质</b>（密码/临时卡）属弱安全，
 * 只能开门锁且应限期有效。
 *
 * <p>四个分类均可实际取到：例如「组织担保 + 密码」= {@code ORG_UNREAL}，
 * 「组织担保 + 指纹」= {@code ORG_REAL}。''')

io.open(P, 'w', encoding='utf-8').write(s)
print('已修正 derive：ORG_VERIFY 不再单独构成实名依据')
