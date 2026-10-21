package com.yundao.bp.grant.iot;

/**
 * IoT 授权客户端抽象。
 *
 * <p>为什么抽象：现网 IoT 的授权接口参数尚未与我们联调确认
 * （见 {@code _验证/IoT对接规范-定稿.md} §6），
 * 因此把"下发"抽成接口，编排逻辑可以先用 {@link MockIotGrantClient} 完整验证，
 * 联调确认后只替换实现，编排代码不用动。
 *
 * <p>可用配置 {@code bp.grant.iot-mode=mock|real} 切换。
 */
public interface IotGrantClient {

    /** 下发授权。 */
    IotGrantResult grant(IotGrantRequest req);

    /** 撤销授权。 */
    IotGrantResult revoke(IotGrantRequest req);

    /** 轮询异步任务结果（{@code iotTaskId} 非空时使用）。 */
    IotGrantResult queryTaskResult(String iotTaskId);
}
