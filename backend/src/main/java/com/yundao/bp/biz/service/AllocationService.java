package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.AllocateCmd;
import com.yundao.bp.biz.dto.AllocationVO;
import com.yundao.bp.biz.dto.BatchCreateCmd;
import com.yundao.bp.biz.dto.BatchVO;
import com.yundao.bp.biz.dto.LotteryResultVO;
import com.yundao.bp.biz.dto.LotteryRunCmd;
import com.yundao.bp.biz.dto.WaitingEnterCmd;
import com.yundao.bp.biz.dto.WaitingVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 配租服务：轮候 → 批次 → 摇号 → 配租。
 *
 * <p><b>主线</b>：
 * <pre>
 *   申请通过 → 入轮候库（算分排名）
 *     → 建批次（草稿 → 发布 → 报名）
 *     → 批次房源入池
 *     → 摇号（种子可复现 + 公证留痕）
 *     → 生成配租单（锁定房源，超时释放）
 *     → 签约（写日房态/合同）
 * </pre>
 */
public interface AllocationService {

    // ---------- 轮候 ----------
    /** 入轮候库（自动算分、生成轮候号）。 */
    WaitingVO enterQueue(WaitingEnterCmd cmd);

    WaitingVO getWaiting(Long id);

    PageResult<WaitingVO> pageWaiting(long pageNum, long pageSize, String securityType,
                                      Long orgId, String status);

    /** 重算轮候排名（总分 = 优先分 + 轮候天数 × 每日分值）。 */
    int recalcRank(String securityType, Long orgId);

    /** 冻结/解冻轮候资格。 */
    WaitingVO freezeWaiting(Long id, String reason);

    WaitingVO unfreezeWaiting(Long id);

    /** 退出轮候。 */
    WaitingVO exitWaiting(Long id, String reason);

    // ---------- 批次 ----------
    BatchVO createBatch(BatchCreateCmd cmd);

    BatchVO getBatch(Long id);

    PageResult<BatchVO> pageBatch(long pageNum, long pageSize, Long orgId, String status);

    /** 批次内加房源。 */
    int addHouses(Long batchId, List<Long> houseIds);

    /** 状态流转（发布/报名/选房/结束等）。 */
    BatchVO transition(Long id, String targetStatus);

    /** 批次房源池。 */
    List<Long> listBatchHouses(Long batchId, String inPoolStatus);

    // ---------- 摇号 ----------
    /**
     * 执行摇号。
     *
     * <p>规则：按轮候总分降序（同分按入队时间升序）取前 N 名中签（N = 房源数），
     * 其余标记 LOST；分数相同的边界用种子随机决定，结果可复现。
     */
    List<LotteryResultVO> runLottery(LotteryRunCmd cmd);

    /** 查询摇号结果（按选房序号排序）。 */
    List<LotteryResultVO> listLotteryResults(Long batchId);

    // ---------- 配租 ----------
    /** 生成配租单（锁定房源）。 */
    AllocationVO allocate(AllocateCmd cmd);

    AllocationVO getAllocation(Long id);

    PageResult<AllocationVO> pageAllocations(long pageNum, long pageSize, Long personId,
                                             Long batchId, String status);

    /** 签约（配租单置已签约，房源池置已选中）。 */
    AllocationVO sign(Long id);

    /** 放弃配租（释放房源回池）。 */
    AllocationVO giveUp(Long id, String reason);

    /** 扫描并释放已超时未签约的配租单，返回释放数。 */
    int releaseExpiredLocks();
}
