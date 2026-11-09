package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.PersonService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform/persons")
public class PersonController {

    private final PersonService service;

    public PersonController(PersonService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam(required = false) String keyword,
                                             @RequestParam(required = false) String personType) {
        return R.ok(service.list(keyword, personType));
    }

    @PostMapping
    public R<Map<String, Object>> create(@RequestBody PersonService.PersonCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @PostMapping("/{personId}/update")
    public R<Map<String, Object>> update(@PathVariable long personId,
                                         @RequestBody PersonService.PersonCmd cmd) {
        return R.ok(service.update(personId, cmd));
    }

    @PostMapping("/{personId}/archive")
    public R<Map<String, Object>> archive(@PathVariable long personId) {
        return R.ok(service.archive(personId));
    }

    @PostMapping("/{personId}/status")
    public R<Map<String, Object>> status(@PathVariable long personId,
                                         @RequestBody Map<String, String> body) {
        return R.ok(service.setStatus(personId, body.get("status")));
    }

    @PostMapping("/{personId}/relations/{relationId}/remove")
    public R<Map<String, Object>> removeRelation(@PathVariable long personId,
                                                 @PathVariable long relationId) {
        return R.ok(service.removeRelation(personId, relationId));
    }

    @GetMapping("/{personId}/relations")
    public R<List<Map<String, Object>>> relations(@PathVariable long personId) {
        return R.ok(service.relations(personId));
    }

    @PostMapping("/{personId}/relations")
    public R<Map<String, Object>> createRelation(@PathVariable long personId,
                                                 @RequestBody PersonService.RelationCmd cmd) {
        return R.ok(service.createRelation(personId, cmd));
    }
}
