package com.yundao.bp.iot.credential;

/**
 * 凭据下发到 IoT（密码/卡/人脸/离线码）。
 *
 * <p>配置 {@code bp.credential.mode=mock|real}；real 实现待 IoT 参数确认。
 */
public interface CredentialSyncClient {

    Result sync(SyncRequest req);

    record SyncRequest(String requestId, Long personId, String keyType, String channelType,
                       String channelValue, String action) {
    }

    record Result(boolean success, String code, String message) {
    }
}
