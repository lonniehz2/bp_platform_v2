package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class ShortRentService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public ShortRentService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select o.id, o.project_id projectId, o.house_id houseId, h.house_name houseName, "
                        + "o.order_no orderNo, o.guest_name guestName, o.guest_phone guestPhone, "
                        + "o.start_date startDate, o.end_date endDate, o.nights, o.amount, "
                        + "o.order_status orderStatus, o.remark, o.create_time createTime "
                        + "from guarantee_short_rent_order o left join bp_house h on h.id=o.house_id "
                        + "where o.tenant_id=? and o.project_id=? and o.is_deleted=0 order by o.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.guestName() == null || cmd.guestName().isBlank()
                || cmd.startDate() == null || cmd.endDate() == null) {
            throw BizException.param("项目、入住人、起止日期不能为空");
        }
        if (!cmd.endDate().isAfter(cmd.startDate())) {
            throw BizException.param("离店日期必须晚于入住日期");
        }
        long nights = ChronoUnit.DAYS.between(cmd.startDate(), cmd.endDate());
        String no = "SR" + System.currentTimeMillis();
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_short_rent_order(id,tenant_id,project_id,house_id,order_no,"
                            + "guest_name,guest_phone,start_date,end_date,nights,amount,order_status,remark,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?, 'PENDING',?,0)",
                    id, TenantContext.require(), cmd.projectId(), cmd.houseId(), no,
                    cmd.guestName().trim(), cmd.guestPhone(), cmd.startDate(), cmd.endDate(), nights,
                    cmd.amount() == null ? BigDecimal.ZERO : cmd.amount(), cmd.remark());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("短租订单号重复");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("orderNo", no);
        out.put("nights", nights);
        out.put("orderStatus", "PENDING");
        return out;
    }

    public Map<String, Object> updateStatus(long id, String status) {
        if (!List.of("CONFIRMED", "CHECKED_IN", "COMPLETED", "CANCELLED").contains(status)) {
            throw BizException.param("短租订单状态不合法");
        }
        long updated = jdbc.update("update guarantee_short_rent_order set order_status=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                status, id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("短租订单不存在");
        }
        return Map.of("id", id, "orderStatus", status);
    }

    public record CreateCmd(Long projectId, Long houseId, String guestName, String guestPhone,
                            LocalDate startDate, LocalDate endDate, BigDecimal amount, String remark) {
    }
}
