package com.yundao.bp.msg.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.msg.dto.TodoOverviewVO;
import com.yundao.bp.msg.service.TodoCenterService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 统一待办中心接口。
 *
 * <p>与 {@link MessageController} 的分工：那边管待办明细的增删改查（读/完成），
 * 这里只提供跨模块的待办计数总览。
 */
@RestController
@RequestMapping("/api/v1/todos")
public class TodoCenterController {

    private final TodoCenterService service;

    public TodoCenterController(TodoCenterService service) {
        this.service = service;
    }

    @GetMapping("/overview")
    public R<TodoOverviewVO> overview() {
        return R.ok(service.overview());
    }
}
