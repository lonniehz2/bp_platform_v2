package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * 设备绑定视图：返回当前空间的直绑设备与从父级继承的设备。
 */
@Service
public class DeviceBindingService {

    private final JdbcTemplate jdbc;

    public DeviceBindingService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> view(long projectId, long spaceId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> spaces = jdbc.queryForList(
                "select id, parent_id parentId, space_name spaceName, space_type spaceType, level_no levelNo "
                        + "from bp_space where tenant_id=? and org_id=? and is_deleted=0",
                tenant, projectId);
        Map<Long, Map<String, Object>> byId = new HashMap<>();
        for (Map<String, Object> sp : spaces) {
            byId.put(((Number) sp.get("id")).longValue(), sp);
        }
        Map<String, Object> current = byId.get(spaceId);
        if (current == null) {
            throw BizException.notFound("空间不存在");
        }
        List<Map<String, Object>> ancestors = new ArrayList<>();
        Map<String, Object> cursor = current;
        while (cursor.get("parentId") != null) {
            Map<String, Object> parent = byId.get(((Number) cursor.get("parentId")).longValue());
            if (parent == null) break;
            ancestors.add(0, parent);
            cursor = parent;
        }
        List<Map<String, Object>> devices = jdbc.queryForList(
                "select id, space_id spaceId, device_code deviceCode, device_name deviceName, device_type deviceType, "
                        + "device_mac deviceMac, install_status installStatus, asset_status assetStatus, business_status businessStatus "
                        + "from bp_dev_device where tenant_id=? and project_id=? and is_deleted=0 order by id",
                tenant, projectId);
        List<Map<String, Object>> direct = new ArrayList<>();
        for (Map<String, Object> d : devices) {
            if (d.get("spaceId") != null && ((Number) d.get("spaceId")).longValue() == spaceId) {
                direct.add(d);
            }
        }
        List<Map<String, Object>> inherited = new ArrayList<>();
        List<Map<String, Object>> path = new ArrayList<>(ancestors);
        path.add(current);
        for (int i = 0; i < ancestors.size(); i++) {
            Map<String, Object> ancestor = ancestors.get(i);
            long ancestorId = ((Number) ancestor.get("id")).longValue();
            String sourcePath = names(path.subList(0, i + 1));
            int level = ((Number) current.get("levelNo")).intValue()
                    - ((Number) ancestor.get("levelNo")).intValue();
            for (Map<String, Object> d : devices) {
                if (d.get("spaceId") != null && ((Number) d.get("spaceId")).longValue() == ancestorId) {
                    Map<String, Object> item = new LinkedHashMap<>(d);
                    item.put("sourceSpaceId", ancestorId);
                    item.put("sourceSpaceName", ancestor.get("spaceName"));
                    item.put("sourcePath", sourcePath);
                    item.put("inheritLevel", level);
                    item.put("bindType", "INHERITED");
                    inherited.add(item);
                }
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("spaceId", spaceId);
        out.put("spaceName", current.get("spaceName"));
        out.put("spaceType", current.get("spaceType"));
        out.put("spacePath", names(path));
        out.put("direct", direct);
        out.put("inherited", inherited);
        return out;
    }

    private static String names(List<Map<String, Object>> nodes) {
        StringBuilder b = new StringBuilder();
        for (Map<String, Object> n : nodes) {
            if (b.length() > 0) b.append(" / ");
            b.append(n.get("spaceName"));
        }
        return b.toString();
    }
}
