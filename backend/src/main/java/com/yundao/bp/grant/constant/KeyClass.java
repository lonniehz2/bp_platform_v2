package com.yundao.bp.grant.constant;

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
 * <p><b>实名介质</b>（人脸/指纹/掌静脉/身份证/人证核验通过）属强安全，
 * 可用于开大门与户门；<b>非实名介质</b>（密码/临时卡）属弱安全，
 * 只能开门锁且应限期有效。
 *
 * <p>四个分类均可实际取到：例如「组织担保 + 密码」= {@code ORG_UNREAL}，
 * 「组织担保 + 指纹」= {@code ORG_REAL}。
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
