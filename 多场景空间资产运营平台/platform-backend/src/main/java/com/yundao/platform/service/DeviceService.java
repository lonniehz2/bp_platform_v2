package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class DeviceService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public DeviceService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select d.id, d.project_id projectId, d.space_id spaceId, s.space_name spaceName, "
                        + "d.device_code deviceCode, d.device_name deviceName, d.device_type deviceType, "
                        + "d.device_model deviceModel, d.device_mac deviceMac, d.is_virtual isVirtual, "
                        + "d.install_status installStatus, d.asset_status assetStatus, d.business_status businessStatus, "
                        + "d.install_time installTime, d.warranty_end warrantyEnd "
                        + "from bp_dev_device d left join bp_space s on s.id=d.space_id "
                        + "where d.tenant_id=? and d.project_id=? and d.is_deleted=0 order by d.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(DeviceCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.projectId() == null || cmd.deviceCode() == null || cmd.deviceCode().isBlank()
                || cmd.deviceName() == null || cmd.deviceName().isBlank()
                || cmd.deviceType() == null || cmd.deviceType().isBlank()) {
            throw BizException.param("项目、设备编码、名称、类型不能为空");
        }
        if (count("select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0",
                cmd.projectId(), tenant) == 0) {
            throw BizException.param("项目不存在");
        }
        if (cmd.spaceId() != null && count("select count(*) from bp_space where id=? and tenant_id=? "
                + "and org_id=? and is_deleted=0", cmd.spaceId(), tenant, cmd.projectId()) == 0) {
            throw BizException.param("设备绑定空间不属于当前项目");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_dev_device(id,tenant_id,project_id,space_id,device_code,device_name,"
                            + "device_type,device_model,asset_status,business_status,install_time,warranty_end,"
                            + "remark,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                    id, tenant, cmd.projectId(), cmd.spaceId(), cmd.deviceCode().trim(),
                    cmd.deviceName().trim(), cmd.deviceType(), cmd.deviceModel(),
                    cmd.assetStatus() == null ? "ACTIVE" : cmd.assetStatus(),
                    cmd.businessStatus() == null ? "IN_USE" : cmd.businessStatus(),
                    cmd.installTime(), cmd.warrantyEnd(), cmd.remark());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("设备编码已存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("deviceCode", cmd.deviceCode());
        out.put("deviceName", cmd.deviceName());
        out.put("assetStatus", cmd.assetStatus() == null ? "ACTIVE" : cmd.assetStatus());
        return out;
    }


    public Map<String, Object> bind(long deviceId, Long spaceId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select project_id projectId from bp_dev_device where id=? and tenant_id=? and is_deleted=0",
                deviceId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("设备不存在");
        }
        long projectId = ((Number) rows.get(0).get("projectId")).longValue();
        if (spaceId != null && count("select count(*) from bp_space where id=? and tenant_id=? and org_id=? and is_deleted=0",
                spaceId, tenant, projectId) == 0) {
            throw BizException.param("空间不属于设备所在项目");
        }
        jdbc.update("update bp_dev_device set space_id=?, update_time=now() where id=? and tenant_id=?",
                spaceId, deviceId, tenant);
        return Map.of("id", deviceId, "spaceId", spaceId == null ? "" : spaceId);
    }

    public Map<String, Object> repair(long deviceId, String reason) {
        String tenant = TenantContext.require();
        int updated = jdbc.update("update bp_dev_device set business_status='FAULT', "
                + "remark=concat(coalesce(remark,''), ?), update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0",
                "\n报修:" + (reason == null ? "" : reason), deviceId, tenant);
        if (updated == 0) throw BizException.notFound("设备不存在");
        return Map.of("id", deviceId, "businessStatus", "FAULT");
    }

    public Map<String, Object> enable(long deviceId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select business_status businessStatus from bp_dev_device "
                        + "where id=? and tenant_id=? and is_deleted=0", deviceId, tenant);
        if (rows.isEmpty()) throw BizException.notFound("设备不存在");
        String status = String.valueOf(rows.get(0).get("businessStatus"));
        if (!"FAULT".equals(status) && !"DISABLED".equals(status)) {
            throw BizException.conflict("只有故障或停用设备可以启用");
        }
        jdbc.update("update bp_dev_device set business_status='IN_USE', update_time=now() "
                + "where id=? and tenant_id=?", deviceId, tenant);
        return Map.of("id", deviceId, "businessStatus", "IN_USE");
    }

    private long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, args);
        return value == null ? 0 : value;
    }


    public Map<String, Object> update(long deviceId, DeviceCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.deviceName() == null || cmd.deviceName().isBlank()) throw BizException.param("设备名称不能为空");
        int updated = jdbc.update("update bp_dev_device set device_name=?, device_type=?, device_model=?, "
                        + "install_time=?, warranty_end=?, remark=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                cmd.deviceName().trim(), cmd.deviceType(), cmd.deviceModel(),
                cmd.installTime(), cmd.warrantyEnd(), cmd.remark(), deviceId, tenant);
        if (updated == 0) throw BizException.notFound("设备不存在");
        return Map.of("id", deviceId, "deviceName", cmd.deviceName());
    }

    public record DeviceCmd(Long projectId, Long spaceId, String deviceCode, String deviceName,
                            String deviceType, String deviceModel, String assetStatus,
                            String businessStatus, java.time.LocalDateTime installTime,
                            LocalDate warrantyEnd, String remark) {
    }
}
