package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.SceneService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform")
public class SceneController {

    private final SceneService sceneService;

    public SceneController(SceneService sceneService) {
        this.sceneService = sceneService;
    }

    @GetMapping("/scenes")
    public R<List<Map<String, Object>>> scenes() {
        return R.ok(sceneService.scenes());
    }

    @GetMapping("/scenes/{sceneCode}/business-modes")
    public R<List<Map<String, Object>>> modes(@PathVariable String sceneCode) {
        return R.ok(sceneService.businessModes(sceneCode));
    }
}
