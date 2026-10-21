package com.yundao.bp.grant.constant;

/**
 * 授权任务状态（对应 {@code bp_grant_task.task_status}）。
 *
 * <pre>
 *   PENDING ──消费者取到──> DISPATCHING ──成功──> SUCCESS
 *      │                        │
 *      │                        ├──部分失败──> PARTIAL
 *      │                        └──失败(可重试)──> PENDING（retryCount++）
 *      │                                              └─超限─> FAILED
 *      └──IoT 返回异步 taskId──> DISPATCHING（等轮询结果）
 * </pre>
 */
public enum GrantTaskStatus {

    PENDING("待下发"),
    DISPATCHING("下发中"),
    SUCCESS("成功"),
    PARTIAL("部分成功"),
    FAILED("失败");

    private final String label;

    GrantTaskStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否已结束（不再重试/轮询）。 */
    public boolean isFinished() {
        return this == SUCCESS || this == PARTIAL || this == FAILED;
    }
}
