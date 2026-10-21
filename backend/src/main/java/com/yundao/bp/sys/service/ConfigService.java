package com.yundao.bp.sys.service;

import com.yundao.bp.sys.entity.SysConfig;
import java.math.BigDecimal;
import java.util.List;

/**
 * 系统参数服务。
 *
 * <p>⭐ <b>核心用途</b>：把政策参数从硬编码改为可配置，支持分地区差异。
 * 优先级：<b>本租户配置 &gt; 全局配置 &gt; 调用方默认值</b>。
 */
public interface ConfigService {

    /** 取字符串参数。 */
    String getString(String key, String defaultValue);

    /** 取整型参数。 */
    int getInt(String key, int defaultValue);

    /** 取小数值。 */
    BigDecimal getDecimal(String key, BigDecimal defaultValue);

    /** 取布尔参数。 */
    boolean getBool(String key, boolean defaultValue);

    /** 按分组列出全部参数。 */
    List<SysConfig> listByGroup(String group);

    /** 全部参数。 */
    List<SysConfig> listAll();

    /** 设置参数（不存在则创建）。 */
    SysConfig set(String key, String value, String description);
}
