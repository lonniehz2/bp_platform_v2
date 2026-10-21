package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.AppealCreateCmd;
import com.yundao.bp.biz.dto.AppealDecisionCmd;
import com.yundao.bp.biz.dto.AppealVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 申诉/异议（复议）服务。
 *
 * <p>⭐ <b>合规意义（决策 D28）</b>：保障房管理可作出「审核不通过 / 年审调租 / 年审退出」
 * 等不利决定，住户必须有<b>申诉与救济通道</b>，否则程序不合法。
 *
 * <p><b>流程</b>：提出 → 受理 → 调查 → 决定（异议成立 / 不成立）→ 告知。
 *
 * <p><b>结果影响</b>：{@code UPHELD} 时可选择恢复资格（RESTORE）、
 * 取消资格（CANCEL）、调整标准（ADJUST）或仅确认无影响（NONE）。
 */
public interface AppealService {

    /** 提出申诉/异议（超出期限拒绝）。 */
    AppealVO submit(AppealCreateCmd cmd);

    AppealVO get(Long id);

    PageResult<AppealVO> page(long pageNum, long pageSize, Long personId, String bizType,
                              String status);

    /** 某业务对象（如年审单）的申诉记录。 */
    List<AppealVO> listByBiz(String bizType, Long bizId);

    /** 受理。 */
    AppealVO accept(Long id, Long acceptUserId);

    /** 进入调查。 */
    AppealVO investigate(Long id, Long handleUserId);

    /** 作出决定（异议成立/不成立 + 结果影响）。 */
    AppealVO decide(Long id, AppealDecisionCmd cmd);

    /** 撤回。 */
    AppealVO withdraw(Long id, String reason);

    /** 标记已告知。 */
    AppealVO markNotified(Long id);

    /** 扫描并标记超期未受理的申诉，返回处理数。 */
    int markTimeout();
}
