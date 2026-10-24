package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.dto.KeyringVO;
import com.yundao.bp.grant.entity.GrantKeyring;
import java.util.List;

/**
 * 钥匙包服务。
 *
 * <p><b>以人为中心管理多介质</b>：一个人可有多把钥匙（人脸/指纹/掌静脉/密码/卡），
 * 按<b>四分类</b>区分安全等级。这是 ★ 级「四级权限」考核的直接落点。
 */
public interface KeyringService {

    /**
     * 新增钥匙。
     *
     * <p>校验：同一人员同类型同别名不可重复；非实名介质必须设有效期。
     */
    KeyringVO add(KeyringCmd cmd);

    /** 某人的钥匙包（含分类统计）。 */
    List<KeyringVO> listByPerson(Long personId);

    /** 一个人的钥匙包概览（四分类各几把、是否满足强安全要求）。 */
    java.util.Map<String, Object> summary(Long personId);

    /** 冻结/解冻。 */
    KeyringVO setStatus(Long id, String status);

    /** 逻辑删除。 */
    KeyringVO remove(Long id);

    PageResult<KeyringVO> page(long pageNum, long pageSize, Long personId, String keyType,
                               String keyClass, String keyStatus);

    GrantKeyring get(Long id);

    /** 新增钥匙入参。 */
    record KeyringCmd(Long personId, String keyType, String keyAlias, String channelValue,
                      String keySource, String verifyWay, String syncScope,
                      String expireTime) {
    }

    /** 冻结钥匙（临时停用，可解冻）。 */
    KeyringVO freeze(Long id);

    /** 解冻钥匙。 */
    KeyringVO unfreeze(Long id);
}
