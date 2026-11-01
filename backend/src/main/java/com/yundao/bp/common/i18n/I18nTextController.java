package com.yundao.bp.common.i18n;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.R;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/** 业务主数据翻译维护接口。 */
@RestController
@RequestMapping("/api/v1/i18n/texts")
public class I18nTextController {

    private final I18nTextService service;

    public I18nTextController(I18nTextService service) {
        this.service = service;
    }

    @GetMapping
    public R<List<Map<String, Object>>> list(@RequestParam(required = false) String locale,
                                             @RequestParam(required = false) String resourceType) {
        String loc = locale == null || locale.isBlank() ? LocaleContext.tag() : locale;
        return R.ok(service.list(loc, resourceType));
    }

    @PostMapping
    public R<Void> upsert(@RequestBody Map<String, Object> body) {
        Object rawId = body.get("resourceId");
        if (rawId == null) {
            return R.fail(ErrorCode.PARAM_MISSING, "resourceId required");
        }
        long id;
        try {
            id = Long.parseLong(String.valueOf(rawId));
        } catch (NumberFormatException e) {
            return R.fail(ErrorCode.PARAM_INVALID, "resourceId invalid");
        }
        service.upsert(str(body.get("resourceType")), id, str(body.get("field")),
                str(body.get("locale")), str(body.get("text")), str(body.get("status")));
        return R.ok();
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v);
    }
}
