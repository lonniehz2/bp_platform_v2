package com.yundao.bp.rpt.service;

import com.yundao.bp.rpt.entity.RptScreenDef;
import java.util.List;
import java.util.Map;

/**
 * 大屏服务：可配置大屏定义 + 实时数据。
 */
public interface ScreenService {

    List<RptScreenDef> listScreens(String screenType);

    RptScreenDef getByCode(String screenCode);

    /**
     * 取大屏数据（按 widget 配置逐项取指标）。
     *
     * @return { screen: 定义, widgets: [ {code,title,chart,value,unit} ] }
     */
    Map<String, Object> data(String screenCode, Long orgId);

    RptScreenDef save(String screenCode, String screenName, String screenType,
                      String layoutConfig, String widgetConfig, Integer refreshSeconds);
}
