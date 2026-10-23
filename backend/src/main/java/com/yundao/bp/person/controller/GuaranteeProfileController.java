package com.yundao.bp.person.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.person.entity.PersonGuaranteeProfile;
import com.yundao.bp.person.service.GuaranteeProfileService;
import com.yundao.bp.sys.audit.Audit;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 保障对象档案接口。
 */
@RestController
@RequestMapping("/api/v1/guarantee-profiles")
public class GuaranteeProfileController {

    private final GuaranteeProfileService service;

    public GuaranteeProfileController(GuaranteeProfileService service) {
        this.service = service;
    }

    /** 建档/更新（同一人员唯一档案）。 */
    @PostMapping
    @RequirePerm("person:profile:manage")
    @Audit(type = "DATA", level = "IMPORTANT", action = "保障对象建档")
    public R<PersonGuaranteeProfile> save(
            @RequestBody GuaranteeProfileService.ProfileCmd cmd) {
        return R.ok(service.save(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:profile:view")
    @GetMapping("/person/{personId}")
    public R<PersonGuaranteeProfile> getByPerson(@PathVariable Long personId) {
        return R.ok(service.getByPerson(personId));
    }

    /** ⭐ 重算收入档位（阈值由调用方传入，支持分地区）。 */
    @PostMapping("/person/{personId}/recalc-income")
    @RequirePerm("person:profile:manage")
    @Audit(type = "DATA", level = "IMPORTANT", action = "重算收入档位")
    public R<Map<String, Object>> recalcIncome(@PathVariable Long personId,
                                               @RequestBody IncomeCmd cmd) {
        return R.ok(service.recalcIncome(personId, cmd.lowLine(), cmd.lowIncomeLine(),
                cmd.middleLowLine()));
    }

    /** 资格审核通过（写资格有效期）。 */
    @PostMapping("/person/{personId}/qualify")
    @RequirePerm("person:profile:manage")
    @Audit(type = "DATA", level = "CRITICAL", action = "资格审核通过")
    public R<PersonGuaranteeProfile> qualify(@PathVariable Long personId,
                                             @RequestParam(required = false)
                                             Integer years) {
        return R.ok(service.qualify(personId, years));
    }

    /** 退出保障。 */
    @PostMapping("/person/{personId}/exit")
    @RequirePerm("person:profile:manage")
    @Audit(type = "DATA", level = "CRITICAL", action = "保障对象退出")
    public R<PersonGuaranteeProfile> exit(@PathVariable Long personId,
                                          @RequestBody ExitCmd cmd) {
        return R.ok(service.exit(personId, cmd.exitDate(), cmd.reason()));
    }

    /** ⭐ 资格到期预警（年审依据）。 */
    @com.yundao.bp.iam.security.RequirePerm("person:profile:view")
    @GetMapping("/expiring")
    public R<List<Map<String, Object>>> expiring(
            @RequestParam(defaultValue = "30") int withinDays) {
        return R.ok(service.expiring(withinDays));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:profile:view")
    @GetMapping
    public R<PageResult<PersonGuaranteeProfile>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String securityType,
            @RequestParam(required = false) String incomeLevel,
            @RequestParam(required = false) String profileStatus,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Long personId) {
        return R.ok(service.page(pageNum, pageSize, securityType, incomeLevel,
                profileStatus, keyword, personId));
    }

    public record IncomeCmd(BigDecimal lowLine, BigDecimal lowIncomeLine,
                            BigDecimal middleLowLine) {
    }

    public record ExitCmd(@DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate exitDate,
                          String reason) {
    }
}
