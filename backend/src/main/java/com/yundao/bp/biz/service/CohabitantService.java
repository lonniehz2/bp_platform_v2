package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.CohabitantCreateCmd;
import com.yundao.bp.biz.dto.CohabitantVO;
import java.util.List;

/**
 * 合同同住人服务。
 *
 * <p>⭐ <b>保障人口口径（决策 D24）</b>：
 * {@code 保障人口 = 承租人 1 人 + 同住人数}。
 * 按人补贴、年审人均收入核查、退租腾退家庭人数均按此口径计算。
 */
public interface CohabitantService {

    /** 添加同住人（同一合同内姓名不可重复）。 */
    CohabitantVO add(Long contractId, CohabitantCreateCmd cmd);

    /** 列同住人。 */
    List<CohabitantVO> list(Long contractId);

    CohabitantVO get(Long id);

    /** 移除同住人。 */
    void remove(Long id);

    /** 设置门禁开门授权。 */
    CohabitantVO setGranted(Long id, boolean granted);

    /**
     * 保障人口数 = 承租人 1 + 同住人数。
     *
     * <p>供按人补贴、年审核查调用。
     */
    int householdSize(Long contractId);
}
