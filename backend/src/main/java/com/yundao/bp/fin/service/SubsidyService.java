package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.dto.SubsidyGrantCmd;
import com.yundao.bp.fin.dto.SubsidyRecordVO;
import com.yundao.bp.fin.dto.SubsidyStandardCreateCmd;
import com.yundao.bp.fin.dto.SubsidyStandardVO;
import java.math.BigDecimal;
import java.util.List;

/**
 * 补贴标准与发放服务（广州"实物配租 + 租赁补贴"双轨支撑）。
 *
 * <p><b>计算口径</b>：
 * <pre>
 *   FIXED    → 金额 = 补贴值
 *   BY_AREA  → 金额 = 单价 × 面积
 *   BY_PERSON→ 金额 = 人均 × 人口
 *   RATIO    → 金额 = 月租金 × 比例
 *   最后统一受 max_amount 封顶
 * </pre>
 */
public interface SubsidyService {

    // ---------- 标准 ----------
    SubsidyStandardVO createStandard(SubsidyStandardCreateCmd cmd);

    SubsidyStandardVO getStandard(Long id);

    PageResult<SubsidyStandardVO> pageStandards(long pageNum, long pageSize, String securityType,
                                                String subsidyMode, String keyword);

    SubsidyStandardVO setStandardStatus(Long id, boolean enabled);

    /** 试算（不落库）。 */
    SubsidyCalcResult preview(SubsidyCalcCmd cmd);

    /** 按所属期试算（补贴与租金同口径）。 */
    SubsidyCalcResult preview(SubsidyCalcCmd cmd, String period);

    // ---------- 发放 ----------
    /** 单户单期发放（自动匹配标准、算金额、建记录）。 */
    SubsidyRecordVO grant(SubsidyGrantCmd cmd);

    SubsidyRecordVO getRecord(Long id);

    PageResult<SubsidyRecordVO> pageRecords(long pageNum, long pageSize, Long contractId,
                                            Long personId, String period, String status);

    /** 批量发放：按期间对全部生效合同（实物配租之外的补贴对象）发放。 */
    BatchResult grantBatch(String subsidyPeriod, Long orgId, String payMode, boolean dryRun);

    /** 确认发放成功（联动：OFFSET_RENT 方式会自动抵扣当期租金账单）。 */
    SubsidyRecordVO confirmPaid(Long id, BigDecimal paidAmount, String financeBatchNo);

    /** 标记发放失败。 */
    SubsidyRecordVO markFailed(Long id, String failReason);

    /** 试算结果。 */
    record SubsidyCalcResult(Long standardId, String standardCode, String subsidyMode,
                             BigDecimal amount, BigDecimal cappedAmount, boolean capped,
                             String explain) {
    }

    /** 批量结果。 */
    record BatchResult(String subsidyPeriod, int total, int granted, int skipped,
                       BigDecimal totalAmount, boolean dryRun, List<String> skipReasons) {
    }
}
