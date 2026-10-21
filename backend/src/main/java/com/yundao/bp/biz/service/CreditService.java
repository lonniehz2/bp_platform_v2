package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.CreditCreateCmd;
import com.yundao.bp.biz.dto.CreditVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 信用惩戒服务。
 *
 * <p>⭐ <b>核心作用（决策 D30）</b>：失信记录必须能<b>真正阻止再申请</b>，
 * 否则惩戒形同虚设。申请受理前应调用 {@link #checkApplyBan} 校验。
 */
public interface CreditService {

    /** 记入失信（自动计算限制申请起止日）。 */
    CreditVO record(CreditCreateCmd cmd);

    CreditVO get(Long id);

    PageResult<CreditVO> page(long pageNum, long pageSize, Long personId, String violationType,
                              String status);

    /** 某人的全部信用记录。 */
    List<CreditVO> listByPerson(Long personId);

    /**
     * 校验是否处于限制申请期。
     *
     * @throws com.yundao.bp.common.exception.BizException 处于限制期则抛出（含解禁日期）
     */
    void checkApplyBan(Long personId);

    /** 当前是否处于限制申请期（不抛异常）。 */
    boolean isUnderBan(Long personId);

    /** 解除（期满）。 */
    CreditVO expire(Long id);

    /** 撤销（复议/纠错）。 */
    CreditVO revoke(Long id, String reason);

    /** 标记推送信用平台成功/失败。 */
    CreditVO markPushed(Long id, boolean success, String platform);

    /** 扫描已过限制期的记录置为已解除，返回处理数。 */
    int scanExpired();
}
