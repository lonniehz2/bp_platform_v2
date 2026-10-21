package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.ops.constant.ComplaintStatus;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsComplaint;
import com.yundao.bp.ops.mapper.OpsComplaintMapper;
import com.yundao.bp.ops.service.ComplaintService;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 投诉建议实现。
 *
 * <p>投诉类默认 48 小时未处理视为超时（VO 派生 {@code overdue}）。
 */
@Service
public class ComplaintServiceImpl implements ComplaintService {

    private static final Logger log = LoggerFactory.getLogger(ComplaintServiceImpl.class);

    private final OpsComplaintMapper mapper;
    private final WorkOrderService workOrderService;
    private final SnowflakeIdGenerator idGen;

    public ComplaintServiceImpl(OpsComplaintMapper mapper, WorkOrderService workOrderService,
                                SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.workOrderService = workOrderService;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO create(ComplaintCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();

        OpsComplaint e = new OpsComplaint();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setComplaintNo("C" + id);
        e.setComplaintType(cmd.complaintType());
        e.setSource(blankToNull(cmd.source()) == null ? "OTHER" : cmd.source());
        e.setOrgId(cmd.orgId());
        e.setPersonId(cmd.personId());
        e.setSubmitterName(cmd.submitterName());
        e.setSubmitterPhone(cmd.submitterPhone());
        e.setTitle(cmd.title());
        e.setContent(cmd.content());
        e.setImages(cmd.images());
        e.setHandleStatus(ComplaintStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return ComplaintVO.from(e);
    }

    @Override
    public ComplaintVO get(Long id) {
        return ComplaintVO.from(require(id));
    }

    @Override
    public PageResult<ComplaintVO> page(long pageNum, long pageSize, String type, String status,
                                        Long orgId, String keyword) {
        LambdaQueryWrapper<OpsComplaint> qw = new LambdaQueryWrapper<OpsComplaint>()
                .eq(type != null && !type.isBlank(), OpsComplaint::getComplaintType, type)
                .eq(status != null && !status.isBlank(), OpsComplaint::getHandleStatus, status)
                .eq(orgId != null, OpsComplaint::getOrgId, orgId)
                .orderByDesc(OpsComplaint::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(OpsComplaint::getTitle, keyword)
                    .or().like(OpsComplaint::getComplaintNo, keyword));
        }
        IPage<OpsComplaint> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ComplaintVO> rows = page.getRecords().stream().map(ComplaintVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO handle(Long id, Long handleUserId) {
        OpsComplaint e = require(id);
        transition(e, ComplaintStatus.HANDLING);
        e.setHandleUserId(handleUserId);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO resolve(Long id, Long handleUserId, String result) {
        OpsComplaint e = require(id);
        transition(e, ComplaintStatus.HANDLED);
        e.setHandleUserId(handleUserId);
        e.setHandleResult(result);
        e.setHandleTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO close(Long id, Long handleUserId) {
        OpsComplaint e = require(id);
        transition(e, ComplaintStatus.CLOSED);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO evaluate(Long id, Integer satisfaction) {
        if (satisfaction == null || satisfaction < 1 || satisfaction > 5) {
            throw BizException.paramInvalid("满意度必须是 1-5");
        }
        OpsComplaint e = require(id);
        if (ComplaintStatus.PENDING.name().equals(e.getHandleStatus())) {
            throw BizException.stateConflict("尚未处理，不能评价");
        }
        e.setSatisfaction(satisfaction);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO toWorkOrder(Long id, Long operatorId, String operatorName) {
        OpsComplaint e = require(id);
        if (e.getWorkorderId() != null) {
            throw BizException.stateConflict("该投诉已转工单（ID=" + e.getWorkorderId() + "）");
        }
        if (ComplaintStatus.CLOSED.name().equals(e.getHandleStatus())) {
            throw BizException.stateConflict("已归档的投诉不能转工单");
        }
        if (ComplaintStatus.PENDING.name().equals(e.getHandleStatus())) {
            transition(e, ComplaintStatus.HANDLING);
        }

        WorkOrderCreateCmd wo = new WorkOrderCreateCmd(
                "COMPLAINT", "STAFF",
                e.getTitle() == null ? "投诉处置" : "【投诉处置】" + e.getTitle(),
                e.getContent(), e.getOrgId(), null, null, null, null, e.getPersonId(),
                e.getSubmitterName(), e.getSubmitterPhone(), null, e.getImages(),
                60, null, "来源投诉：" + e.getComplaintNo());
        WorkOrderVO created = workOrderService.create(wo);

        e.setWorkorderId(created.id());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("投诉 {} 转工单 {}", e.getComplaintNo(), created.workorderNo());
        return ComplaintVO.from(e);
    }

    private OpsComplaint require(Long id) {
        OpsComplaint e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("投诉建议");
        }
        return e;
    }

    private static void transition(OpsComplaint e, ComplaintStatus target) {
        ComplaintStatus from;
        try {
            from = ComplaintStatus.valueOf(e.getHandleStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("投诉状态非法: " + e.getHandleStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ComplaintStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setHandleStatus(target.name());
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
