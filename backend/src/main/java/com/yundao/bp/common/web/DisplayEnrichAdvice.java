package com.yundao.bp.common.web;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import org.springframework.core.MethodParameter;
import org.springframework.http.MediaType;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

import java.util.List;
import java.util.Map;

/**
 * 统一响应补全：在序列化前给分页/列表结果补上名称与中文标签。
 *
 * <p>为什么放在这一层：显示层缺陷（界面上出现 {@code 370832686538952704}、
 * {@code ALLOCATED}）散落在几十个接口，逐个改 VO 既慢又容易漏。
 * 在此统一处理，**新写的接口自动获得补全能力**。</p>
 *
 * <p>安全性：只对 {@link PageResult} 与 {@code List} 生效，
 * 且只**追加**字段，原字段原样保留，不影响任何调用方。</p>
 */
@RestControllerAdvice
public class DisplayEnrichAdvice implements ResponseBodyAdvice<Object> {

    private final DisplayEnricher enricher;

    public DisplayEnrichAdvice(DisplayEnricher enricher) {
        this.enricher = enricher;
    }

    @Override
    public boolean supports(MethodParameter returnType, Class converterType) {
        return true;
    }

    /** 只有对象/Map 才需要补中文名；字符串/数字/布尔等标量列表直接返回 */
    private static boolean isEnrichable(Object first) {
        if (first == null) {
            return false;
        }
        return !(first instanceof CharSequence) && !(first instanceof Number)
                && !(first instanceof Boolean) && !(first instanceof Map<?, ?>);
    }

    @Override
    public Object beforeBodyWrite(Object body, MethodParameter returnType,
                                  MediaType selectedContentType,
                                  Class selectedConverterType,
                                  ServerHttpRequest request,
                                  ServerHttpResponse response) {
        if (!(body instanceof R<?> r) || r.data() == null) {
            return body;
        }
        Object data = r.data();
        if (data instanceof PageResult<?> pr) {
            PageResult<java.util.Map<String, Object>> enriched =
                    new PageResult<>(pr.total(), pr.pageNum(), pr.pageSize(),
                            enricher.enrichRows(pr.rows()));
            return new R<>(r.code(), r.message(), enriched, r.timestamp());
        }
        if (data instanceof List<?> list && !list.isEmpty()
                && isEnrichable(list.get(0))) {
            return new R<>(r.code(), r.message(), enricher.enrichRows(list), r.timestamp());
        }
        return body;
    }
}
