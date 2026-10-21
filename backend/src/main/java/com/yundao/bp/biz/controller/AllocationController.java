package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.AllocateCmd;
import com.yundao.bp.biz.dto.AllocationVO;
import com.yundao.bp.biz.dto.BatchCreateCmd;
import com.yundao.bp.biz.dto.BatchVO;
import com.yundao.bp.biz.dto.LotteryResultVO;
import com.yundao.bp.biz.dto.LotteryRunCmd;
import com.yundao.bp.biz.dto.WaitingEnterCmd;
import com.yundao.bp.biz.dto.WaitingVO;
import com.yundao.bp.biz.service.AllocationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 配租接口（BC-05）：轮候 → 批次 → 摇号 → 配租。
 */
@RestController
@RequestMapping("/api/v1/allocation")
public class AllocationController {

    private final AllocationService service;

    public AllocationController(AllocationService service) {
        this.service = service;
    }

    // ---------- 轮候 ----------

    /** 申请通过后入轮候库。 */
    @PostMapping("/waiting")
    public R<WaitingVO> enter(@Valid @RequestBody WaitingEnterCmd cmd) {
        return R.ok(service.enterQueue(cmd));
    }

    @GetMapping("/waiting/{id}")
    public R<WaitingVO> getWaiting(@PathVariable Long id) {
        return R.ok(service.getWaiting(id));
    }

    @GetMapping("/waiting")
    public R<PageResult<WaitingVO>> pageWaiting(@RequestParam(defaultValue = "1") long pageNum,
                                                @RequestParam(defaultValue = "20") long pageSize,
                                                @RequestParam(required = false) String securityType,
                                                @RequestParam(required = false) Long orgId,
                                                @RequestParam(required = false) String status) {
        return R.ok(service.pageWaiting(pageNum, pageSize, securityType, orgId, status));
    }

    /** 重算轮候排名。 */
    @PostMapping("/waiting/recalc")
    public R<Integer> recalc(@RequestParam(required = false) String securityType,
                             @RequestParam(required = false) Long orgId) {
        return R.ok(service.recalcRank(securityType, orgId));
    }

    @PostMapping("/waiting/{id}/freeze")
    public R<WaitingVO> freeze(@PathVariable Long id,
                               @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.freezeWaiting(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/waiting/{id}/unfreeze")
    public R<WaitingVO> unfreeze(@PathVariable Long id) {
        return R.ok(service.unfreezeWaiting(id));
    }

    @PostMapping("/waiting/{id}/exit")
    public R<WaitingVO> exit(@PathVariable Long id,
                             @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.exitWaiting(id, cmd == null ? null : cmd.reason()));
    }

    // ---------- 批次 ----------

    @PostMapping("/batches")
    public R<BatchVO> createBatch(@Valid @RequestBody BatchCreateCmd cmd) {
        return R.ok(service.createBatch(cmd));
    }

    @GetMapping("/batches/{id}")
    public R<BatchVO> getBatch(@PathVariable Long id) {
        return R.ok(service.getBatch(id));
    }

    @GetMapping("/batches")
    public R<PageResult<BatchVO>> pageBatch(@RequestParam(defaultValue = "1") long pageNum,
                                            @RequestParam(defaultValue = "20") long pageSize,
                                            @RequestParam(required = false) Long orgId,
                                            @RequestParam(required = false) String status) {
        return R.ok(service.pageBatch(pageNum, pageSize, orgId, status));
    }

    /** 批次加房源。 */
    @PostMapping("/batches/{id}/houses")
    public R<Integer> addHouses(@PathVariable Long id, @RequestBody HousesCmd cmd) {
        return R.ok(service.addHouses(id, cmd.houseIds()));
    }

    @GetMapping("/batches/{id}/houses")
    public R<List<Long>> listHouses(@PathVariable Long id,
                                    @RequestParam(required = false) String inPoolStatus) {
        return R.ok(service.listBatchHouses(id, inPoolStatus));
    }

    /** 状态流转（PUBLISHED / SIGNUP / SELECTING / CLOSED / CANCELLED）。 */
    @PostMapping("/batches/{id}/status")
    public R<BatchVO> transition(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(service.transition(id, cmd.batchStatus()));
    }

    // ---------- 摇号 ----------

    /** 执行摇号（种子可复现、公证留痕）。 */
    @PostMapping("/lottery")
    public R<List<LotteryResultVO>> lottery(@Valid @RequestBody LotteryRunCmd cmd) {
        return R.ok(service.runLottery(cmd));
    }

    @GetMapping("/lottery/{batchId}")
    public R<List<LotteryResultVO>> lotteryResults(@PathVariable Long batchId) {
        return R.ok(service.listLotteryResults(batchId));
    }

    // ---------- 配租 ----------

    /** 生成配租单（锁定房源）。 */
    @PostMapping("/allocations")
    public R<AllocationVO> allocate(@Valid @RequestBody AllocateCmd cmd) {
        return R.ok(service.allocate(cmd));
    }

    @GetMapping("/allocations/{id}")
    public R<AllocationVO> getAllocation(@PathVariable Long id) {
        return R.ok(service.getAllocation(id));
    }

    @GetMapping("/allocations")
    public R<PageResult<AllocationVO>> pageAllocations(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) Long batchId,
            @RequestParam(required = false) String status) {
        return R.ok(service.pageAllocations(pageNum, pageSize, personId, batchId, status));
    }

    /** 签约。 */
    @PostMapping("/allocations/{id}/sign")
    public R<AllocationVO> sign(@PathVariable Long id) {
        return R.ok(service.sign(id));
    }

    /** 放弃配租（释放房源）。 */
    @PostMapping("/allocations/{id}/give-up")
    public R<AllocationVO> giveUp(@PathVariable Long id,
                                  @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.giveUp(id, cmd == null ? null : cmd.reason()));
    }

    /** 扫描释放超时未签约的房源。 */
    @PostMapping("/allocations/release-expired")
    public R<Integer> releaseExpired() {
        return R.ok(service.releaseExpiredLocks());
    }

    public record ReasonCmd(String reason) {
    }

    public record HousesCmd(List<Long> houseIds) {
    }

    public record StatusCmd(String batchStatus) {
    }
}
