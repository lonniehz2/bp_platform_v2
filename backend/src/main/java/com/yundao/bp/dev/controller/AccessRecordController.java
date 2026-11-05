package com.yundao.bp.dev.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.dev.dto.AccessReportCmd;
import com.yundao.bp.dev.dto.AccessVO;
import com.yundao.bp.dev.dto.IdleStatVO;
import com.yundao.bp.dev.dto.TraceVO;
import com.yundao.bp.dev.service.AccessRecordService;
import com.yundao.bp.iam.security.RequirePerm;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 通行记录接口（BC-04）。
 *
 * <p>数据源：IoT 开门回调写入 / 定时拉取补齐。支撑行为轨迹、空置判定、异常开门告警。
 */
@RestController
@RequestMapping("/api/v1/access-records")
public class AccessRecordController {

    private final AccessRecordService service;

    public AccessRecordController(AccessRecordService service) {
        this.service = service;
    }

    /** 上报一条（供 IoT 回调或补偿）。 */
    @PostMapping
    @RequirePerm("dev:access:report")
    public R<Boolean> report(@Valid @RequestBody AccessReportCmd cmd) {
        return R.ok(service.report(cmd));
    }

    /** 批量上报。 */
    @PostMapping("/batch")
    @RequirePerm("dev:access:report")
    public R<Integer> reportBatch(@Valid @RequestBody List<AccessReportCmd> cmds) {
        return R.ok(service.reportBatch(cmds));
    }

    @com.yundao.bp.iam.security.RequirePerm("access-records:access-records:view")
    @GetMapping
    public R<PageResult<AccessVO>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo,
            @RequestParam(required = false) Boolean abnormalOnly,
            @RequestParam(required = false) String openType) {
        return R.ok(service.page(pageNum, pageSize, personId, houseId, dateFrom, dateTo,
                abnormalOnly, openType));
    }

    /** ⭐ 人员行为轨迹。 */
    @com.yundao.bp.iam.security.RequirePerm("access-records:trace:view")
    @GetMapping("/trace/person/{personId}")
    public R<TraceVO> tracePerson(
            @org.springframework.web.bind.annotation.PathVariable Long personId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.traceByPerson(personId, dateFrom, dateTo));
    }

    /** ⭐ 房源行为轨迹。 */
    @com.yundao.bp.iam.security.RequirePerm("access-records:trace:view")
    @GetMapping("/trace/house/{houseId}")
    public R<TraceVO> traceHouse(
            @org.springframework.web.bind.annotation.PathVariable Long houseId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.traceByHouse(houseId, dateFrom, dateTo));
    }

    /** ⭐ 空置判定。 */
    @com.yundao.bp.iam.security.RequirePerm("access-records:idle:view")
    @GetMapping("/idle")
    public R<List<IdleStatVO>> idle(@RequestParam(required = false) Long orgId,
                                    @RequestParam(defaultValue = "30") int idleDays) {
        return R.ok(service.detectIdle(orgId, idleDays));
    }

    /** 不可信开门占比（考核指标）。 */
    @com.yundao.bp.iam.security.RequirePerm("access-records:untrusted-ratio:view")
    @GetMapping("/untrusted-ratio")
    public R<Map<String, Object>> untrustedRatio(
            @RequestParam(required = false) Long orgId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(service.untrustedRatio(orgId, dateFrom, dateTo));
    }
}
