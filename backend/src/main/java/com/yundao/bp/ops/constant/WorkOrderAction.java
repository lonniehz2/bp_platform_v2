package com.yundao.bp.ops.constant;

/**
 * 工单流转动作（对应 {@code bp_ops_workorder_log.action}）。
 */
public enum WorkOrderAction {

    CREATE("创建"),
    ASSIGN("派单"),
    ACCEPT("接单"),
    START("开始处理"),
    FINISH("完工"),
    CLOSE("闭环"),
    CANCEL("取消"),
    REJECT("驳回"),
    EVALUATE("评价"),
    REMARK("备注");

    private final String label;

    WorkOrderAction(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
