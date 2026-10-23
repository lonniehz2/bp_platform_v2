package com.yundao.bp.person.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.person.dto.PersonCreateCmd;
import com.yundao.bp.person.dto.PersonVO;
import com.yundao.bp.person.service.PersonService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 人员档案接口（BC-03）。
 *
 * <p>⚠️ 返回的 {@link PersonVO} 只含脱敏数据，不含身份证/手机号原文。
 */
@RestController
@RequestMapping("/api/v1/persons")
public class PersonController {

    private final PersonService personService;

    public PersonController(PersonService personService) {
        this.personService = personService;
    }

    @com.yundao.bp.iam.security.RequirePerm("person:person:create")
    @PostMapping
    public R<PersonVO> create(@Valid @RequestBody PersonCreateCmd cmd) {
        return R.ok(personService.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:person:view")
    @GetMapping("/{id}")
    public R<PersonVO> get(@PathVariable Long id) {
        return R.ok(personService.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:person:view")
    @GetMapping
    public R<PageResult<PersonVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                        @RequestParam(defaultValue = "20") long pageSize,
                                        @RequestParam(required = false) String keyword,
                                        @RequestParam(required = false) Long orgId,
                                        @RequestParam(required = false) String personStatus,
            @RequestParam(required = false) Boolean includeChildren) {
        return R.ok(personService.page(pageNum, pageSize, keyword, orgId, personStatus,
                includeChildren));
    }

    /** 按身份证号精确查找（走哈希列）。未找到返回 null 而非 404。 */
    @com.yundao.bp.iam.security.RequirePerm("person:person:view")
    @GetMapping("/by-id-card")
    public R<PersonVO> byIdCard(@RequestParam String idCard) {
        return R.ok(personService.findByIdCard(idCard));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:person:update")
    @PutMapping("/{id}")
    public R<PersonVO> update(@PathVariable Long id,
                              @Valid @RequestBody com.yundao.bp.person.dto.PersonUpdateCmd cmd) {
        return R.ok(personService.update(id, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:person:status")
    @PostMapping("/{id}/status")
    public R<PersonVO> changeStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(personService.changeStatus(id, cmd.status()));
    }

    @com.yundao.bp.iam.security.RequirePerm("person:person:delete")
    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        personService.delete(id);
        return R.ok();
    }

    public record StatusCmd(String status) {
    }
}
