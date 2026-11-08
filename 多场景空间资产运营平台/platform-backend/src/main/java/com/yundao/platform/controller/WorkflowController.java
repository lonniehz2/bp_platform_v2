package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.WorkflowService;
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
@RequestMapping("/api/v1/platform")
public class WorkflowController {

    private final WorkflowService service;

    public WorkflowController(WorkflowService service) {
        this.service = service;
    }

    @GetMapping("/workflows")
    public R<List<Map<String, Object>>> flows(@RequestParam(required = false) String sceneCode,
                                              @RequestParam(required = false) String bizType) {
        return R.ok(service.flows(sceneCode, bizType));
    }

    @PostMapping("/workflows")
    public R<Map<String, Object>> createFlow(@RequestBody WorkflowService.FlowCmd cmd) {
        return R.ok(service.createFlow(cmd));
    }

    @PostMapping("/workflows/{flowId}/submit")
    public R<Map<String, Object>> submit(@PathVariable long flowId,
                                         @RequestBody WorkflowService.SubmitCmd cmd) {
        return R.ok(service.submit(flowId, cmd));
    }

    @GetMapping("/workflow-tasks")
    public R<List<Map<String, Object>>> tasks(@RequestParam(required = false) String status) {
        return R.ok(service.tasks(status));
    }

    @PostMapping("/workflow-tasks/{taskId}/approve")
    public R<Map<String, Object>> approve(@PathVariable long taskId,
                                          @RequestBody WorkflowService.ActionCmd cmd) {
        return R.ok(service.approve(taskId, cmd));
    }

    @PostMapping("/workflow-tasks/{taskId}/reject")
    public R<Map<String, Object>> reject(@PathVariable long taskId,
                                         @RequestBody WorkflowService.ActionCmd cmd) {
        return R.ok(service.reject(taskId, cmd));
    }

    @GetMapping("/workflow-tasks/{taskId}/records")
    public R<List<Map<String, Object>>> records(@PathVariable long taskId) {
        return R.ok(service.records(taskId));
    }
}
