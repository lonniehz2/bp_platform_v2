package com.yundao.bp.iam.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.ops.entity.OpsAlert;
import com.yundao.bp.ops.entity.OpsWorkorder;
import com.yundao.bp.ops.mapper.OpsAlertMapper;
import com.yundao.bp.ops.mapper.OpsWorkorderMapper;
import com.yundao.bp.fin.entity.FinArrearsAction;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.mapper.FinArrearsActionMapper;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.msg.entity.MsgTodo;
import com.yundao.bp.msg.mapper.MsgTodoMapper;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 菜单角标：一次返回各菜单项需要提醒的数量。
 *
 * <p>供左侧菜单显示「待办 N / 逾期 N / 待派单 N」等徽标，
 * 避免用户逐个点开才知道有没有活。
 */
@RestController
@RequestMapping("/api/v1/menu")
public class MenuBadgeController {

    private final MsgTodoMapper todoMapper;
    private final FinBillMapper billMapper;
    private final FinArrearsActionMapper arrearsMapper;
    private final OpsAlertMapper alertMapper;
    private final OpsWorkorderMapper workOrderMapper;

    public MenuBadgeController(MsgTodoMapper todoMapper,
                               FinBillMapper billMapper,
                               FinArrearsActionMapper arrearsMapper,
                               OpsAlertMapper alertMapper,
                               OpsWorkorderMapper workOrderMapper) {
        this.todoMapper = todoMapper;
        this.billMapper = billMapper;
        this.arrearsMapper = arrearsMapper;
        this.alertMapper = alertMapper;
        this.workOrderMapper = workOrderMapper;
    }

    /** 五类计数；任一查询失败返回 0，不影响其他角标。 */
    @GetMapping("/badges")
    public R<Map<String, Long>> badges() {
        Map<String, Long> out = new LinkedHashMap<>();
        out.put("todo", countTodo());
        out.put("overdueBills", countOverdueBills());
        out.put("pendingArrears", countPendingArrears());
        out.put("pendingAlerts", countPendingAlerts());
        out.put("pendingWorkOrders", countPendingWorkOrders());
        return R.ok(out);
    }

    private long countTodo() {
        try {
            Long userId = TenantContext.userId();
            LambdaQueryWrapper<MsgTodo> qw = new LambdaQueryWrapper<MsgTodo>()
                    .ne(MsgTodo::getTodoStatus, "DONE");
            if (userId != null) {
                qw.eq(MsgTodo::getUserId, userId);
            }
            Long n = todoMapper.selectCount(qw);
            return n == null ? 0 : n;
        } catch (Exception e) {
            return 0;
        }
    }

    private long countOverdueBills() {
        try {
            Long n = billMapper.selectCount(new LambdaQueryWrapper<FinBill>()
                    .eq(FinBill::getBillStatus, "OVERDUE"));
            return n == null ? 0 : n;
        } catch (Exception e) {
            return 0;
        }
    }

    private long countPendingArrears() {
        try {
            Long n = arrearsMapper.selectCount(new LambdaQueryWrapper<FinArrearsAction>()
                    .eq(FinArrearsAction::getActionStatus, "PENDING"));
            return n == null ? 0 : n;
        } catch (Exception e) {
            return 0;
        }
    }

    private long countPendingAlerts() {
        try {
            Long n = alertMapper.selectCount(new LambdaQueryWrapper<OpsAlert>()
                    .eq(OpsAlert::getAlertStatus, "PENDING"));
            return n == null ? 0 : n;
        } catch (Exception e) {
            return 0;
        }
    }

    private long countPendingWorkOrders() {
        try {
            Long n = workOrderMapper.selectCount(new LambdaQueryWrapper<OpsWorkorder>()
                    .eq(OpsWorkorder::getOrderStatus, "PENDING"));
            return n == null ? 0 : n;
        } catch (Exception e) {
            return 0;
        }
    }
}
