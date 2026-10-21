package com.yundao.bp.msg.dto;

import java.util.List;

/**
 * 统一待办中心总览。
 *
 * <p>只做「聚合计数 + 跳转指引」，不复制各模块的业务明细——明细点进去看原页面，
 * 避免两套数据口径打架。
 *
 * @param total      各分类之和
 * @param categories 分类待办
 */
public record TodoOverviewVO(long total, List<Category> categories) {

    /**
     * @param key   分类标识
     * @param label 中文名
     * @param count 待办数量
     * @param route 前端路由（点击卡片跳转）
     * @param hint  一句话说明该分类要做什么
     */
    public record Category(String key, String label, long count, String route, String hint) {
    }
}
