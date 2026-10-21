package com.yundao.bp.msg.service.impl;

import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.msg.dto.TodoOverviewVO;
import com.yundao.bp.msg.service.TodoCenterService;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * 待办聚合实现。
 *
 * <p><b>为什么用 JdbcTemplate 而不是各模块的 Mapper</b>：这里是跨 7 张表的只读计数，
 * 引 7 个 Mapper 反而把模块边界搅乱；SQL 里显式带 {@code tenant_id} 保证多租户隔离
 * （JdbcTemplate 不走租户拦截器，必须手写）。
 *
 * <p><b>容错</b>：单张表查询失败（缺表、状态值不匹配）只记一条 warn，该分类计 0，
 * 不让一个模块拖垮整个待办中心。
 */
@Service
public class TodoCenterServiceImpl implements TodoCenterService {

    private static final Logger log = LoggerFactory.getLogger(TodoCenterServiceImpl.class);

    private final JdbcTemplate jdbc;

    public TodoCenterServiceImpl(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /** 一个待办分类的查询定义。 */
    private record Def(String key, String label, String table, String where,
                       boolean softDelete, String route, String hint) {
    }

    /**
     * 各分类的「待办」判定口径。
     *
     * <p>口径说明：只统计「需要人动手」的状态，已通过/已完成的不算待办。
     */
    private static final List<Def> DEFS = List.of(
            new Def("TODO", "待办消息", "bp_msg_todo",
                    "todo_status = 'PENDING'", false,
                    "/messages?pending=1", "站内指派给你的任务与提醒"),
            new Def("APPLICATION", "待审申请", "bp_biz_application",
                    "application_status in ('SUBMITTED','ACCEPTED','REVIEWING','SUPPLEMENT')", true,
                    "/applications?pending=1", "受理、审核、补正材料"),
            new Def("CONTRACT", "待签合同", "bp_biz_contract",
                    "contract_status in ('PENDING_SIGN','SIGNING')", true,
                    "/contracts?pending=1", "推进签约直至履约"),
            new Def("TERMINATION", "待处理退租", "bp_biz_termination",
                    "termination_status in ('APPLYING','APPROVING','APPROVED')", false,
                    "/terminations?pending=1", "审批、查验、结算、放房源"),
            new Def("EXCHANGE", "待审换房", "bp_biz_exchange",
                    "exchange_status in ('APPLYING','APPROVING','APPROVED')", false,
                    "/exchanges?pending=1", "换房审核与执行"),
            new Def("REVIEW", "待复核年审", "bp_biz_annual_review",
                    "review_status in ('PENDING','REVIEWING','OVERDUE')", false,
                    "/annual-reviews?pending=1", "资格年审复核"),
            new Def("WORKORDER", "待处理工单", "bp_ops_workorder",
                    "order_status in ('PENDING','PROCESSING')", true,
                    "/ops-center?tab=order&pending=1", "接单、处置、回访")
    );

    @Override
    public TodoOverviewVO overview() {
        String tenant = TenantContext.tenantId();
        List<TodoOverviewVO.Category> out = new ArrayList<>(DEFS.size());
        long total = 0;
        for (Def d : DEFS) {
            long n = count(d, tenant);
            total += n;
            out.add(new TodoOverviewVO.Category(d.key(), d.label(), n, d.route(), d.hint()));
        }
        return new TodoOverviewVO(total, out);
    }

    private long count(Def d, String tenant) {
        String sql = "select count(*) from " + d.table()
                + " where tenant_id = ? and " + d.where()
                + (d.softDelete() ? " and (is_deleted = 0 or is_deleted is null)" : "");
        try {
            Long n = jdbc.queryForObject(sql, Long.class, tenant);
            return n == null ? 0L : n;
        } catch (DataAccessException e) {
            log.warn("待办分类 [{}] 统计失败，按 0 处理：{}", d.label(), e.getMessage());
            return 0L;
        }
    }
}
