package com.yundao.bp.ops.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.i18n.MessageResolver;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.ops.entity.OpsAlert;
import com.yundao.bp.ops.mapper.OpsAlertMapper;
import com.yundao.bp.sys.service.ConfigService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 每日自动巡查：长期未开门、低电量、合同到期、设备离线、长期闲置。
 *
 * <p>阈值全部走系统参数，管理员可调；同类型+同对象已有待处理告警时不重复生成。
 */
@Component
public class DailyPatrolJob {

    private static final Logger log = LoggerFactory.getLogger(DailyPatrolJob.class);

    private final JdbcTemplate jdbc;
    private final OpsAlertMapper alertMapper;
    private final IamTenantMapper tenantMapper;
    private final ConfigService configService;
    private final MessageResolver messages;
    private final SnowflakeIdGenerator idGen;

    public DailyPatrolJob(JdbcTemplate jdbc, OpsAlertMapper alertMapper,
                          IamTenantMapper tenantMapper, ConfigService configService,
                          MessageResolver messages, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.alertMapper = alertMapper;
        this.tenantMapper = tenantMapper;
        this.configService = configService;
        this.messages = messages;
        this.idGen = idGen;
    }

    @Scheduled(cron = "${bp.ops.patrol.cron:0 0 2 * * *}")
    public void runDaily() {
        if (!configService.getBool("patrol.enabled", true)) {
            return;
        }
        runAll();
    }

    /** 手工补跑/测试入口。 */
    public Map<String, Object> runAll() {
        int total = 0;
        int tenants = 0;
        for (IamTenant tenant : tenantMapper.selectList(
                new LambdaQueryWrapper<IamTenant>()
                        .eq(IamTenant::getStatus, "ENABLED")
                        .eq(IamTenant::getDeleted, 0))) {
            if (tenant.getTenantCode() == null || tenant.getTenantCode().isBlank()) {
                continue;
            }
            TenantContext.set(TenantInfo.of(tenant.getTenantCode()));
            try {
                total += runTenant(tenant.getTenantCode());
                tenants++;
            } catch (Exception e) {
                log.warn("Daily patrol failed tenant={}: {}", tenant.getTenantCode(), e.getMessage());
            } finally {
                TenantContext.clear();
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("tenants", tenants);
        out.put("alerts", total);
        return out;
    }

    private int runTenant(String tenantId) {
        int n = 0;
        int noOpenDays = configService.getInt("patrol.noOpenDays", 30);
        int lowBattery = configService.getInt("patrol.lowBatteryPercent", 20);
        int expireDays = configService.getInt("patrol.contractExpireDays", 30);
        int offlineHours = configService.getInt("patrol.deviceOfflineHours", 24);
        int idleDays = configService.getInt("patrol.idleDays", 30);

        // 长期未开门
        List<Map<String, Object>> noOpen = jdbc.queryForList(
                "select c.id contractId, c.contract_no contractNo, c.org_id orgId, "
                        + "c.house_id houseId, c.space_id spaceId, c.lessee_person_id personId, "
                        + "c.lessee_name lesseeName, max(a.open_time) lastOpen "
                        + "from bp_biz_contract c left join bp_dev_access_record a "
                        + "on a.house_id = c.house_id and a.open_time >= c.lease_start "
                        + "where c.contract_status = 'EFFECTIVE' and c.is_deleted = 0 "
                        + "group by c.id, c.contract_no, c.org_id, c.house_id, c.space_id, "
                        + "c.lessee_person_id, c.lessee_name, c.lease_start "
                        + "having (lastOpen is null and c.lease_start <= date_sub(curdate(), interval ? day)) "
                        + "or lastOpen < date_sub(now(), interval ? day)",
                noOpenDays, noOpenDays);
        for (Map<String, Object> r : noOpen) {
            n += add(tenantId, "VIOLATION", "NO_OPEN", "IMPORTANT",
                    messages.get("patrol.noOpen.title"),
                    messages.get("patrol.noOpen.content", noOpenDays),
                    noOpenDays + "d", r, null);
        }

        // 合同即将到期
        List<Map<String, Object>> expiring = jdbc.queryForList(
                "select id contractId, contract_no contractNo, org_id orgId, house_id houseId, "
                        + "space_id spaceId, lessee_person_id personId, lessee_name lesseeName, lease_end leaseEnd "
                        + "from bp_biz_contract where contract_status = 'EFFECTIVE' and is_deleted = 0 "
                        + "and lease_end between curdate() and date_add(curdate(), interval ? day)",
                expireDays);
        for (Map<String, Object> r : expiring) {
            n += add(tenantId, "BUSINESS", "CONTRACT_EXPIRE", "IMPORTANT",
                    messages.get("patrol.expire.title"),
                    messages.get("patrol.expire.content", expireDays),
                    expireDays + "d", r, null);
        }

        // 低电量
        List<Map<String, Object>> low = jdbc.queryForList(
                "select device_id deviceId, device_name deviceName, org_id orgId, "
                        + "space_id spaceId, battery from bp_dev_device "
                        + "where is_deleted = 0 and battery is not null and battery <= ?", lowBattery);
        for (Map<String, Object> r : low) {
            n += add(tenantId, "DEVICE", "LOW_BATTERY", "IMPORTANT",
                    messages.get("patrol.battery.title"),
                    messages.get("patrol.battery.content", lowBattery),
                    lowBattery + "%", r, String.valueOf(r.get("deviceId")));
        }

        // 设备离线
        List<Map<String, Object>> offline = jdbc.queryForList(
                "select device_id deviceId, device_name deviceName, org_id orgId, space_id spaceId, "
                        + "offline_time offlineTime from bp_dev_device where is_deleted = 0 "
                        + "and online_status = 0 and offline_time is not null "
                        + "and offline_time < date_sub(now(), interval ? hour)", offlineHours);
        for (Map<String, Object> r : offline) {
            n += add(tenantId, "DEVICE", "DEVICE_OFFLINE", "IMPORTANT",
                    messages.get("patrol.offline.title"),
                    messages.get("patrol.offline.content", offlineHours),
                    offlineHours + "h", r, String.valueOf(r.get("deviceId")));
        }

        // 长期闲置：门锁长期无开门 + 水电表长期无读数
        List<Map<String, Object>> idle = jdbc.queryForList(
                "select c.id contractId, c.contract_no contractNo, c.org_id orgId, "
                        + "c.house_id houseId, c.space_id spaceId, c.lessee_person_id personId, "
                        + "c.lessee_name lesseeName, max(a.open_time) lastOpen, max(m.read_date) lastRead "
                        + "from bp_biz_contract c "
                        + "left join bp_dev_access_record a on a.house_id = c.house_id and a.open_time >= c.lease_start "
                        + "left join bp_fin_meter_reading m on m.house_id = c.house_id and m.is_deleted = 0 "
                        + "where c.contract_status = 'EFFECTIVE' and c.is_deleted = 0 "
                        + "group by c.id, c.contract_no, c.org_id, c.house_id, c.space_id, "
                        + "c.lessee_person_id, c.lessee_name, c.lease_start "
                        + "having (lastOpen is null and c.lease_start <= date_sub(curdate(), interval ? day)) "
                        + "or (lastOpen < date_sub(now(), interval ? day) "
                        + "and lastRead is not null and lastRead < date_sub(curdate(), interval ? day))",
                idleDays, idleDays, idleDays);
        for (Map<String, Object> r : idle) {
            n += add(tenantId, "VIOLATION", "IDLE", "IMPORTANT",
                    messages.get("patrol.idle.title"),
                    messages.get("patrol.idle.content", idleDays),
                    idleDays + "d", r, null);
        }
        if (n > 0) {
            log.info("Daily patrol tenant={}: {} alerts generated", tenantId, n);
        }
        return n;
    }

    private int add(String tenantId, String category, String type, String level,
                    String title, String content, String threshold,
                    Map<String, Object> r, String deviceId) {
        Long houseId = toLong(r.get("houseId"));
        Long contractId = toLong(r.get("contractId"));
        Long orgId = toLong(r.get("orgId"));
        Long spaceId = toLong(r.get("spaceId"));
        Long personId = toLong(r.get("personId"));
        if (exists(tenantId, type, houseId, contractId, deviceId)) {
            return 0;
        }
        OpsAlert a = new OpsAlert();
        a.setId(idGen.nextId());
        a.setTenantId(tenantId);
        a.setAlertNo("PA" + a.getId());
        a.setAlertCategory(category);
        a.setAlertType(type);
        a.setAlertLevel(level);
        a.setAlertTitle(title);
        a.setAlertContent(content);
        a.setAlertValue(threshold);
        a.setThresholdValue(threshold);
        a.setOrgId(orgId);
        a.setSpaceId(spaceId);
        a.setHouseId(houseId);
        a.setPersonId(personId);
        a.setDeviceId(deviceId);
        a.setContractId(contractId);
        a.setAlertStatus("PENDING");
        a.setAlertTime(LocalDateTime.now());
        a.setCreateTime(LocalDateTime.now());
        alertMapper.insert(a);
        return 1;
    }

    private boolean exists(String tenantId, String type, Long houseId, Long contractId, String deviceId) {
        Long n = jdbc.queryForObject(
                "select count(*) from bp_ops_alert where tenant_id = ? and alert_type = ? "
                        + "and alert_status = 'PENDING' and (house_id <=> ?) "
                        + "and (contract_id <=> ?) and (device_id <=> ?)",
                Long.class, tenantId, type, houseId, contractId, deviceId);
        return n != null && n > 0;
    }

    private static Long toLong(Object v) {
        if (v == null) {
            return null;
        }
        if (v instanceof Number n) {
            return n.longValue();
        }
        try {
            return Long.valueOf(String.valueOf(v));
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
