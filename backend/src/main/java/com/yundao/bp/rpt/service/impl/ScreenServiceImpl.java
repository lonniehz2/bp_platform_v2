package com.yundao.bp.rpt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.rpt.entity.RptScreenDef;
import com.yundao.bp.rpt.mapper.RptScreenDefMapper;
import com.yundao.bp.rpt.service.MetricService;
import com.yundao.bp.rpt.service.ScreenService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 大屏实现。
 *
 * <p>大屏是<b>配置驱动</b>的：{@code widget_config} 描述要哪些指标、
 * 用什么图表；本服务按配置逐项取实时值返回，前端只负责渲染。
 */
@Service
public class ScreenServiceImpl implements ScreenService {

    private static final Logger log = LoggerFactory.getLogger(ScreenServiceImpl.class);

    /** 默认组件配置（未配置时的兜底） */
    private static final String DEFAULT_WIDGETS = """
            [
              {"code":"HOUSE_TOTAL","title":"房源总数","chart":"NUMBER"},
              {"code":"OCCUPANCY_RATE","title":"出租率(%)","chart":"GAUGE"},
              {"code":"HOUSE_VACANT","title":"空置房源","chart":"NUMBER"},
              {"code":"BILL_UNPAID_COUNT","title":"欠费账单","chart":"NUMBER"},
              {"code":"BILL_UNPAID_AMOUNT","title":"欠费金额","chart":"NUMBER"},
              {"code":"PAYMENT_TOTAL_AMOUNT","title":"累计收款","chart":"NUMBER"},
              {"code":"ACCESS_TODAY_COUNT","title":"今日开门","chart":"NUMBER"},
              {"code":"ACCESS_ABNORMAL_COUNT","title":"今日异常开门","chart":"NUMBER"}
            ]""";

    private final RptScreenDefMapper mapper;
    private final MetricService metricService;
    private final SnowflakeIdGenerator idGen;

    public ScreenServiceImpl(RptScreenDefMapper mapper, MetricService metricService,
                             SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.metricService = metricService;
        this.idGen = idGen;
    }

    @Override
    public List<RptScreenDef> listScreens(String screenType) {
        return mapper.selectList(new LambdaQueryWrapper<RptScreenDef>()
                .eq(screenType != null && !screenType.isBlank(),
                        RptScreenDef::getScreenType, screenType)
                .eq(RptScreenDef::getScreenStatus, "ENABLED")
                .orderByAsc(RptScreenDef::getScreenCode));
    }

    @Override
    public RptScreenDef getByCode(String screenCode) {
        RptScreenDef d = mapper.selectOne(new LambdaQueryWrapper<RptScreenDef>()
                .eq(RptScreenDef::getScreenCode, screenCode)
                .last("LIMIT 1"));
        if (d == null) {
            throw BizException.notFound("大屏定义");
        }
        return d;
    }

    @Override
    public Map<String, Object> data(String screenCode, Long orgId) {
        RptScreenDef def = getByCode(screenCode);
        String widgetsJson = def.getWidgetConfig();
        if (widgetsJson == null || widgetsJson.isBlank()) {
            widgetsJson = DEFAULT_WIDGETS;
        }
        List<Map<String, Object>> out = new ArrayList<>();
        try {
            List<Map<String, Object>> defs = new com.fasterxml.jackson.databind.ObjectMapper()
                    .readValue(widgetsJson, List.class);
            // 先收集配置里真正需要的指标编码，只算这些（避免计算无用指标）
            List<String> codes = new ArrayList<>();
            for (Map<String, Object> w : defs) {
                String c = String.valueOf(w.get("code"));
                if (!codes.contains(c)) {
                    codes.add(c);
                }
            }
            Map<String, Object> all = metricService.values(codes, orgId);
            for (Map<String, Object> w : defs) {
                String code = String.valueOf(w.get("code"));
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("code", code);
                item.put("title", w.get("title"));
                item.put("chart", w.get("chart") == null ? "NUMBER" : w.get("chart"));
                Object v = all.get(code);
                item.put("value", v == null ? 0.0 : v);
                out.add(item);
            }
        } catch (Exception ex) {
            log.warn("大屏组件配置解析失败，回退默认：{}", ex.getMessage());
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("screenCode", def.getScreenCode());
        m.put("screenName", def.getScreenName());
        m.put("screenType", def.getScreenType());
        m.put("refreshSeconds", def.getRefreshSeconds());
        m.put("layoutConfig", def.getLayoutConfig());
        m.put("widgets", out);
        m.put("generatedAt", LocalDateTime.now().toString());
        return m;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RptScreenDef save(String screenCode, String screenName, String screenType,
                             String layoutConfig, String widgetConfig,
                             Integer refreshSeconds) {
        RptScreenDef exist = mapper.selectOne(new LambdaQueryWrapper<RptScreenDef>()
                .eq(RptScreenDef::getScreenCode, screenCode)
                .last("LIMIT 1"));
        if (exist != null) {
            if (layoutConfig != null) {
                exist.setLayoutConfig(layoutConfig);
            }
            if (widgetConfig != null) {
                exist.setWidgetConfig(widgetConfig);
            }
            if (refreshSeconds != null) {
                exist.setRefreshSeconds(refreshSeconds);
            }
            exist.setUpdateTime(LocalDateTime.now());
            mapper.updateById(exist);
            return exist;
        }
        RptScreenDef d = new RptScreenDef();
        d.setId(idGen.nextId());
        d.setTenantId(TenantContext.tenantId());
        d.setScreenCode(screenCode);
        d.setScreenName(screenName);
        d.setScreenType(screenType == null ? "OVERVIEW" : screenType);
        d.setLayoutConfig(layoutConfig);
        d.setWidgetConfig(widgetConfig == null ? DEFAULT_WIDGETS : widgetConfig);
        d.setRefreshSeconds(refreshSeconds == null ? 60 : refreshSeconds);
        d.setScreenStatus("ENABLED");
        d.setIsDeleted(0);
        d.setCreateTime(LocalDateTime.now());
        d.setUpdateTime(LocalDateTime.now());
        mapper.insert(d);
        return d;
    }
}
