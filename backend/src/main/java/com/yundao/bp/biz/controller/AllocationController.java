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
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:create")
    @PostMapping("/waiting")
    public R<WaitingVO> enter(@Valid @RequestBody WaitingEnterCmd cmd) {
        return R.ok(service.enterQueue(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:view")
    @GetMapping("/waiting/{id}")
    public R<WaitingVO> getWaiting(@PathVariable Long id) {
        return R.ok(service.getWaiting(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:view")
    @GetMapping("/waiting")
    public R<PageResult<WaitingVO>> pageWaiting(@RequestParam(defaultValue = "1") long pageNum,
                                                @RequestParam(defaultValue = "20") long pageSize,
                                                @RequestParam(required = false) String securityType,
                                                @RequestParam(required = false) Long orgId,
                                                @RequestParam(required = false) String status,
                                                @RequestParam(required = false) String keyword) {
        return R.ok(service.pageWaiting(pageNum, pageSize, securityType, orgId, status,
                keyword));
    }

    /** 重算轮候排名。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:calc")
    @PostMapping("/waiting/recalc")
    public R<Integer> recalc(@RequestParam(required = false) String securityType,
                             @RequestParam(required = false) Long orgId) {
        return R.ok(service.recalcRank(securityType, orgId));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:freeze")
    @PostMapping("/waiting/{id}/freeze")
    public R<WaitingVO> freeze(@PathVariable Long id,
                               @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.freezeWaiting(id, cmd == null ? null : cmd.reason()));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:freeze")
    @PostMapping("/waiting/{id}/unfreeze")
    public R<WaitingVO> unfreeze(@PathVariable Long id) {
        return R.ok(service.unfreezeWaiting(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:create")
    @PostMapping("/waiting/{id}/exit")
    public R<WaitingVO> exit(@PathVariable Long id,
                             @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.exitWaiting(id, cmd == null ? null : cmd.reason()));
    }

    // ---------- 批次 ----------

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @PostMapping("/batches")
    public R<BatchVO> createBatch(@Valid @RequestBody BatchCreateCmd cmd) {
        return R.ok(service.createBatch(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @GetMapping("/batches/{id}")
    public R<BatchVO> getBatch(@PathVariable Long id) {
        return R.ok(service.getBatch(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @GetMapping("/batches")
    public R<PageResult<BatchVO>> pageBatch(@RequestParam(defaultValue = "1") long pageNum,
                                            @RequestParam(defaultValue = "20") long pageSize,
                                            @RequestParam(required = false) Long orgId,
                                            @RequestParam(required = false) String status) {
        return R.ok(service.pageBatch(pageNum, pageSize, orgId, status));
    }

    /** 批次加房源。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @PostMapping("/batches/{id}/houses")
    public R<Integer> addHouses(@PathVariable Long id, @RequestBody HousesCmd cmd) {
        return R.ok(service.addHouses(id, cmd.houseIds()));
    }

    /** 批次房源明细（编号/名称/状态），用于界面展示。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @GetMapping("/batches/{id}/houses/detail")
    public R<java.util.List<java.util.Map<String, Object>>> listHouseDetails(@PathVariable Long id) {
        return R.ok(service.listBatchHouseDetails(id));
    }

    /** 从批次移除房源。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @PostMapping("/batches/{id}/houses/remove")
    public R<Integer> removeHouses(@PathVariable Long id, @RequestBody HousesCmd cmd) {
        return R.ok(service.removeHouses(id, cmd.houseIds()));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @GetMapping("/batches/{id}/houses")
    public R<List<Long>> listHouses(@PathVariable Long id,
                                    @RequestParam(required = false) String inPoolStatus) {
        return R.ok(service.listBatchHouses(id, inPoolStatus));
    }

    /** 摇号完成后生成配租单。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @PostMapping("/batches/{id}/generate-allocations")
    public R<Integer> generateAllocations(@PathVariable Long id) {
        return R.ok(service.generateAllocations(id));
    }

    /** 状态流转（PUBLISHED / SIGNUP / SELECTING / CLOSED / CANCELLED）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @PostMapping("/batches/{id}/status")
    public R<BatchVO> transition(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(service.transition(id, cmd.batchStatus()));
    }

    // ---------- 摇号 ----------

    /** 执行摇号（种子可复现、公证留痕）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:create")
    @PostMapping("/lottery")
    public R<List<LotteryResultVO>> lottery(@RequestBody Object body) {
        // 兼容三种请求体：{batchId:...} / "batchId" / {batchId:{id:...}}
        Object bid;
        String seed = null;
        String notary = null;
        if (body instanceof java.util.Map<?, ?> m) {
            bid = m.get("batchId");
            seed = m.get("seed") == null ? null : String.valueOf(m.get("seed"));
            notary = m.get("notaryInfo") == null ? null : String.valueOf(m.get("notaryInfo"));
        } else {
            bid = body;
        }
        return R.ok(service.runLottery(new LotteryRunCmd(bid, seed, notary)));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:batch")
    @GetMapping("/lottery/{batchId}")
    public R<List<LotteryResultVO>> lotteryResults(@PathVariable Long batchId) {
        return R.ok(service.listLotteryResults(batchId));
    }

    // ---------- 配租 ----------

    /** 生成配租单（锁定房源）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:create")
    @PostMapping("/allocations")
    public R<AllocationVO> allocate(@Valid @RequestBody AllocateCmd cmd) {
        return R.ok(service.allocate(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:view")
    @GetMapping("/allocations/{id}")
    public R<AllocationVO> getAllocation(@PathVariable Long id) {
        return R.ok(service.getAllocation(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:view")
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
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:sign")
    @PostMapping("/allocations/{id}/sign")
    public R<AllocationVO> sign(@PathVariable Long id) {
        return R.ok(service.sign(id));
    }

    /** 放弃配租（释放房源）。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:create")
    @PostMapping("/allocations/{id}/give-up")
    public R<AllocationVO> giveUp(@PathVariable Long id,
                                  @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.giveUp(id, cmd == null ? null : cmd.reason()));
    }

    /** 扫描释放超时未签约的房源。 */
    @com.yundao.bp.iam.security.RequirePerm("biz:allocation:create")
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
