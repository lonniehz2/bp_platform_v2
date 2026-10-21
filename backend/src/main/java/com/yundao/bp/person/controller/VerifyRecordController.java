package com.yundao.bp.person.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.person.entity.PersonVerifyRecord;
import com.yundao.bp.person.service.VerifyRecordService;
import com.yundao.bp.sys.audit.Audit;
import java.math.BigDecimal;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 实名认证留痕接口（只追加，无改删）。
 */
@RestController
@RequestMapping("/api/v1/verify-records")
public class VerifyRecordController {

    private final VerifyRecordService service;

    public VerifyRecordController(VerifyRecordService service) {
        this.service = service;
    }

    /** ⭐ 写入一次认证结果（由认证调用方回写）。 */
    @PostMapping
    @RequirePerm("person:verify:record")
    @Audit(type = "SECURITY", level = "CRITICAL", action = "记录实名认证结果")
    public R<PersonVerifyRecord> record(@RequestBody VerifyCmd cmd) {
        return R.ok(service.record(cmd.personId(), cmd.verifyType(), cmd.userName(),
                cmd.idCardHash(), cmd.faceImgUrl(), cmd.idcardImgUrl(), cmd.commandId(),
                cmd.responseCode(), cmd.resultCode(), cmd.faceScore(),
                cmd.faceResult(), cmd.citizenResult(), cmd.rawResponse()));
    }

    @GetMapping("/{id}")
    public R<PersonVerifyRecord> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<PersonVerifyRecord>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) String verifyType,
            @RequestParam(required = false) Boolean passOnly,
            @RequestParam(required = false) String keyword) {
        return R.ok(service.page(pageNum, pageSize, personId, verifyType, passOnly, keyword));
    }

    /** ⭐ 认证结论（申请校验时用）。 */
    @GetMapping("/person/{personId}/conclusion")
    public R<Map<String, Object>> conclusion(@PathVariable Long personId) {
        return R.ok(service.conclusion(personId));
    }

    /** 失败原因分布（风控看板）。 */
    @GetMapping("/fail-stats")
    @RequirePerm("person:verify:record")
    public R<Map<String, Object>> failStats() {
        return R.ok(service.failStats());
    }

    public record VerifyCmd(Long personId, String verifyType, String userName,
                            String idCardHash, String faceImgUrl, String idcardImgUrl,
                            String commandId, String responseCode, String resultCode,
                            BigDecimal faceScore, String faceResult, String citizenResult,
                            String rawResponse) {
    }
}
