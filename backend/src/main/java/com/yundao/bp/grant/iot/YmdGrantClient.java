package com.yundao.bp.grant.iot;

import com.fasterxml.jackson.core.type.TypeReference;
import com.yundao.bp.iot.legacy.YmdClient;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 云门道 IoT 授权客户端（真实实现）。
 *
 * <p>⚠️ <b>状态：骨架，参数待与 IoT 方联调确认</b>。
 * 端点已从接口文档确认存在：
 * <ul>
 *   <li>{@code /ymd/restful/channel/auth/action} —— 人员授权</li>
 *   <li>{@code /ymd/restful/auth/action} —— 通用介质授权（含人脸）</li>
 *   <li>{@code /ymd/restful/auth/delAuthById} —— 删除授权</li>
 *   <li>{@code /ymd/restful/syncTask/result/list} —— 异步任务结果查询</li>
 *   <li>{@code /ymd/restful/user/add} —— 人员添加（授权前置）</li>
 * </ul>
 *
 * <p><b>待确认项</b>（见 {@code _验证/IoT对接规范-定稿.md} §6）：
 * 各接口的具体参数名、门锁标识用 {@code lockId} 还是 {@code mac}、
 * 有效期字段格式、是否按 lockId 逐个下发。
 *
 * <p>因此本实现仅按最可能的参数拼装，<b>未经真实环境验证</b>，
 * 联调时需逐项核对。默认不启用（{@code bp.grant.iot-mode=mock}）。
 */
public class YmdGrantClient implements IotGrantClient {

    private static final Logger log = LoggerFactory.getLogger(YmdGrantClient.class);
    private static final DateTimeFormatter FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private static final String PATH_PERSON_AUTH = "/ymd/restful/channel/auth/action";
    private static final String PATH_AUTH_ACTION = "/ymd/restful/auth/action";
    private static final String PATH_DEL_AUTH = "/ymd/restful/auth/delAuthById";
    private static final String PATH_TASK_RESULT = "/ymd/restful/syncTask/result/list";

    private final YmdClient client;

    public YmdGrantClient(YmdClient client) {
        this.client = client;
        log.warn("IoT 授权使用真实实现：参数尚未联调确认，请核对后再上线");
    }

    @Override
    public IotGrantResult grant(IotGrantRequest req) {
        try {
            Map<String, String> p = new HashMap<>();
            if (req.iotOwnerId() != null) {
                p.put("ownerId", req.iotOwnerId());
            }
            if (req.account() != null) {
                p.put("account", req.account());
            }
            // TODO 联调确认：门锁列表字段名（lockIds / lockid / macList）
            p.put("lockIds", String.join(",", req.lockIds()));
            if (req.validStart() != null) {
                p.put("validStart", req.validStart().format(FMT));
            }
            if (req.validEnd() != null) {
                p.put("validEnd", req.validEnd().format(FMT));
            }
            if (req.channelType() != null) {
                p.put("channelType", req.channelType());
            }
            if (req.channelModuleType() != null) {
                p.put("channelModuleType", req.channelModuleType());
            }

            String path = req.channelType() == null ? PATH_PERSON_AUTH : PATH_AUTH_ACTION;
            String raw = client.callRaw(path, p);
            // TODO 联调确认：响应结构（iotTaskId 字段名可能是 taskId / data.taskId）
            String taskId = com.yundao.bp.iot.legacy.YmdJsonPublic.extract(raw, "taskId");
            return IotGrantResult.ok(taskId, "已提交", List.of());
        } catch (Exception e) {
            log.warn("IoT 授权下发失败: {}", e.getMessage());
            return IotGrantResult.fail(e.getMessage());
        }
    }

    @Override
    public IotGrantResult revoke(IotGrantRequest req) {
        try {
            Map<String, String> p = new HashMap<>();
            if (req.iotOwnerId() != null) {
                p.put("ownerId", req.iotOwnerId());
            }
            p.put("lockIds", String.join(",", req.lockIds()));
            String raw = client.callRaw(PATH_DEL_AUTH, p);
            return IotGrantResult.ok(null, "撤销已提交: " + brief(raw), List.of());
        } catch (Exception e) {
            return IotGrantResult.fail(e.getMessage());
        }
    }

    @Override
    public IotGrantResult queryTaskResult(String iotTaskId) {
        try {
            Map<String, String> p = new HashMap<>();
            p.put("taskId", iotTaskId);
            String raw = client.callRaw(PATH_TASK_RESULT, p);
            return IotGrantResult.ok(iotTaskId, brief(raw), List.of());
        } catch (Exception e) {
            return IotGrantResult.fail(e.getMessage());
        }
    }

    private static String brief(String s) {
        return s == null ? "" : (s.length() > 200 ? s.substring(0, 200) + "..." : s);
    }
}
