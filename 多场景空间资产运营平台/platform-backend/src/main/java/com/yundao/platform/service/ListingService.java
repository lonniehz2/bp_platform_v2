package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class ListingService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public ListingService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> listings(long projectId) {
        return jdbc.queryForList(
                "select l.id, l.project_id projectId, l.house_id houseId, h.house_code houseCode, "
                        + "h.house_name houseName, l.title, l.description, l.monthly_rent monthlyRent, "
                        + "l.deposit_amount depositAmount, l.cover_url coverUrl, l.listing_status listingStatus, l.publish_time publishTime, "
                        + "(select count(*) from bp_booking b where b.listing_id=l.id and b.is_deleted=0) bookingCount "
                        + "from bp_listing l join bp_house h on h.id=l.house_id "
                        + "where l.tenant_id=? and l.project_id=? and l.is_deleted=0 order by l.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.projectId() == null || cmd.houseId() == null || cmd.title() == null
                || cmd.title().isBlank() || cmd.monthlyRent() == null
                || cmd.monthlyRent().signum() <= 0) {
            throw BizException.param("项目、房屋、标题、月租金不能为空");
        }
        Long house = jdbc.queryForObject(
                "select count(*) from bp_house where id=? and tenant_id=? and org_id=? and is_deleted=0",
                Long.class, cmd.houseId(), tenant, cmd.projectId());
        if (house == null || house == 0) {
            throw BizException.param("房屋不属于当前项目");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_listing(id,tenant_id,project_id,house_id,title,description,"
                            + "monthly_rent,deposit_amount,cover_url,listing_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,'DRAFT',0)",
                    id, tenant, cmd.projectId(), cmd.houseId(), cmd.title().trim(), cmd.description(),
                    cmd.monthlyRent(), cmd.depositAmount() == null ? BigDecimal.ZERO : cmd.depositAmount(),
                    cmd.coverUrl());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("该房屋已有展示记录");
        }
        return Map.of("id", id, "listingStatus", "DRAFT");
    }

    public Map<String, Object> publish(long listingId) {
        int updated = jdbc.update("update bp_listing set listing_status='PUBLISHED', publish_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0",
                listingId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("展示记录不存在");
        return Map.of("id", listingId, "listingStatus", "PUBLISHED");
    }

    public Map<String, Object> offline(long listingId) {
        int updated = jdbc.update("update bp_listing set listing_status='OFFLINE' "
                + "where id=? and tenant_id=? and is_deleted=0", listingId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("展示记录不存在");
        return Map.of("id", listingId, "listingStatus", "OFFLINE");
    }

    public Map<String, Object> book(long listingId, BookingCmd cmd) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> listings = jdbc.queryForList(
                "select project_id projectId, listing_status listingStatus from bp_listing "
                        + "where id=? and tenant_id=? and is_deleted=0", listingId, tenant);
        if (listings.isEmpty()) throw BizException.notFound("展示记录不存在");
        if (!"PUBLISHED".equals(String.valueOf(listings.get(0).get("listingStatus")))) {
            throw BizException.conflict("房源未发布，不能预约");
        }
        if (cmd.personId() == null) throw BizException.param("预约人不能为空");
        long id = idGen.nextId();
        String no = "BK" + System.currentTimeMillis() + id % 1000;
        jdbc.update("insert into bp_booking(id,tenant_id,project_id,listing_id,person_id,booking_no,"
                        + "booking_status,contact_phone,remark,is_deleted) values(?,?,?,?,?,?, 'PENDING',?,?,0)",
                id, tenant, ((Number) listings.get(0).get("projectId")).longValue(), listingId,
                cmd.personId(), no, cmd.contactPhone(), cmd.remark());
        return Map.of("id", id, "bookingNo", no, "bookingStatus", "PENDING");
    }

    public List<Map<String, Object>> bookings(long projectId) {
        return jdbc.queryForList(
                "select b.id, b.booking_no bookingNo, b.listing_id listingId, l.title, "
                        + "b.person_id personId, p.person_name personName, b.booking_status bookingStatus, "
                        + "b.contact_phone contactPhone, b.remark, b.create_time createTime "
                        + "from bp_booking b join bp_listing l on l.id=b.listing_id "
                        + "left join bp_person p on p.id=b.person_id "
                        + "where b.tenant_id=? and b.project_id=? and b.is_deleted=0 order by b.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> updateBooking(long bookingId, String status) {
        if (!List.of("CONFIRMED", "CANCELLED").contains(status)) {
            throw BizException.param("预约状态不合法");
        }
        int updated = jdbc.update("update bp_booking set booking_status=? "
                + "where id=? and tenant_id=? and is_deleted=0", status, bookingId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("预约记录不存在");
        return Map.of("id", bookingId, "bookingStatus", status);
    }

    public record CreateCmd(Long projectId, Long houseId, String title, String description,
                            BigDecimal monthlyRent, BigDecimal depositAmount, String coverUrl) {
    }

    public record BookingCmd(Long personId, String contactPhone, String remark) {
    }
}
