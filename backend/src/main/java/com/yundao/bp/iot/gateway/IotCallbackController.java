package com.yundao.bp.iot.gateway;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * IoT 平台回调统一入口。
 *
 * <p>路径：{@code /api/callback/iot/{action}}，action 见 {@code IotCallbackService#dispatch}。
 * 该路径不走登录鉴权，改用 HMAC 验签 + Nonce 防重放。
 */
@RestController
@RequestMapping("/api/callback/iot")
public class IotCallbackController {

    private final IotCallbackService service;

    public IotCallbackController(IotCallbackService service) {
        this.service = service;
    }

    @PostMapping("/{action:.+}")
    public ResponseEntity<Map<String, Object>> callback(
            @PathVariable String action,
            @RequestBody(required = false) String body,
            HttpServletRequest req) {
        return doHandle(action, body, req);
    }

    /** 带斜杠的动作单独映射（Spring 3 的 PathPattern 下通配不跨层级）。 */
    @PostMapping("/command/ack")
    public ResponseEntity<Map<String, Object>> commandAck(
            @RequestBody(required = false) String body, HttpServletRequest req) {
        return doHandle("command/ack", body, req);
    }

    @PostMapping("/grant/ack")
    public ResponseEntity<Map<String, Object>> grantAck(
            @RequestBody(required = false) String body, HttpServletRequest req) {
        return doHandle("grant/ack", body, req);
    }

    private ResponseEntity<Map<String, Object>> doHandle(String action, String body,
                                                         HttpServletRequest req) {
        IotCallbackService.Reply reply = service.handle(
                action,
                body == null ? "{}" : body,
                req.getHeader("X-Iot-AppId"),
                req.getHeader("X-Iot-Timestamp"),
                req.getHeader("X-Iot-Nonce"),
                req.getHeader("X-Iot-Signature"),
                req.getRemoteAddr(),
                req.getHeader("X-Tenant-Id"));
        return ResponseEntity.status(reply.httpStatus()).body(reply.body());
    }
}
