package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.AssetModelService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform")
public class AssetModelController {

    private final AssetModelService service;

    public AssetModelController(AssetModelService service) {
        this.service = service;
    }

    @GetMapping("/space-templates")
    public R<List<Map<String, Object>>> templates(@RequestParam(required = false) String sceneCode) {
        return R.ok(service.templates(sceneCode));
    }

    @PostMapping("/space-templates")
    public R<Map<String, Object>> createTemplate(
            @RequestBody AssetModelService.TemplateCmd cmd) {
        return R.ok(service.createTemplate(cmd));
    }

    @GetMapping("/asset-types")
    public R<List<Map<String, Object>>> assetTypes(@RequestParam(required = false) String sceneCode) {
        return R.ok(service.assetTypes(sceneCode));
    }

    @PostMapping("/asset-types")
    public R<Map<String, Object>> createAssetType(
            @RequestBody AssetModelService.AssetTypeCmd cmd) {
        return R.ok(service.createAssetType(cmd));
    }
}
