package com.yundao.bp.grant.iot;

import java.util.List;

/** IoT 授权冻结/恢复客户端。真实平台按人员授权解析钥匙包并逐钥匙下发。 */
public interface IotAuthorizationClient {

    IotAuthorizationResult freeze(IotAuthorizationRequest req);

    IotAuthorizationResult unfreeze(IotAuthorizationRequest req);

    record IotAuthorizationRequest(Long houseId, Long personId, Long grantId,
                                   List<Long> keyringIds, String scope, String reason) {
    }

    record IotAuthorizationResult(String orderNo, boolean success, String message) {
        public static IotAuthorizationResult ok(String orderNo) {
            return new IotAuthorizationResult(orderNo, true, "accepted");
        }
    }
}
