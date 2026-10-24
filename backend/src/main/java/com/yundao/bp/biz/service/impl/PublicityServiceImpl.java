package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.PublicityStatus;
import com.yundao.bp.biz.constant.PublicityType;
import com.yundao.bp.biz.dto.PublicityCreateCmd;
import com.yundao.bp.biz.dto.PublicityVO;
import com.yundao.bp.biz.entity.BizPublicity;
import com.yundao.bp.biz.mapper.BizPublicityMapper;
import com.yundao.bp.biz.service.PublicityService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.constant.ConfigKeys;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 公示实现。
 *
 * <p><b>合规规则</b>：配租公示至少 7 个自然日；公示未结束不得签约。
 */
@Service
public class PublicityServiceImpl implements PublicityService {

    private static final Logger log = LoggerFactory.getLogger(PublicityServiceImpl.class);

    /** 配租公示最短公示期默认值（可被系统参数覆盖） */
    private static final int DEFAULT_MIN_ALLOCATION_DAYS = 7;
    /** 系统参数（政策参数可配置） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.sys.service.ConfigService configService;

    private int cfgInt(String key, int def) {
        return configService == null ? def : configService.getInt(key, def);
    }

    private java.math.BigDecimal cfgDec(String key, String def) {
        return configService == null ? new java.math.BigDecimal(def)
                : configService.getDecimal(key, new java.math.BigDecimal(def));
    }


    private final BizPublicityMapper mapper;
    private final SnowflakeIdGenerator idGen;


    /** 人员（中签人姓名/脱敏证件） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonMapper winnerPersonMapper;

    /** 摇号结果 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizLotteryResultMapper winnerLotteryMapper;

    /** 房源（中签房号） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper winnerHouseMapper;


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol,
            boolean full) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(personCol, -1L);
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if (!full) {
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }

    /** 仅组织维度的数据范围（实体无人员列时使用）。 */
    private <T> void applyDataScopeOrg(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.eq(orgCol, -1L);   // 仅本人角色无组织级数据
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }

    public PublicityServiceImpl(BizPublicityMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PublicityVO create(PublicityCreateCmd cmd) {
        if (cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.paramInvalid("公示结束日期不能早于开始日期");
        }
        PublicityType tp;
        try {
            tp = PublicityType.valueOf(cmd.publicityType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("公示类型不合法: " + cmd.publicityType());
        }
        long days = ChronoUnit.DAYS.between(cmd.startDate(), cmd.endDate()) + 1;
        // 配租公示必须满 7 个自然日（含首尾）
        int minDays = cfgInt(ConfigKeys.PUBLICITY_ALLOC_MIN_DAYS,
                DEFAULT_MIN_ALLOCATION_DAYS);
        if (tp == PublicityType.ALLOCATION && days < minDays) {
            throw BizException.paramInvalid(
                    "配租公示期不得少于 " + minDays + " 个自然日，当前仅 "
                            + days + " 天（" + cmd.startDate() + " ~ " + cmd.endDate() + "）");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizPublicity e = new BizPublicity();
        e.setId(id);
        e.setTenantId(TenantContext.tenantId());
        e.setPublicityNo("PB" + id);
        e.setPublicityType(tp.name());
        e.setOrgId(cmd.orgId());
        e.setBatchId(cmd.batchId());   // 关联批次，用于公示中签名单
        e.setTitle(cmd.title());
        e.setContent(cmd.content());
        e.setStartDate(cmd.startDate());
        e.setEndDate(cmd.endDate());
        e.setAttachmentUrl(cmd.attachmentUrl());
        e.setPublicityStatus(PublicityStatus.DRAFT.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("公示创建 {}：{} {}~{}（{} 天）", e.getPublicityNo(), tp.label(),
                cmd.startDate(), cmd.endDate(), days);
        return PublicityVO.from(e);
    }

    @Override
    public PublicityVO get(Long id) {
        return PublicityVO.from(require(id));
    }

    @Override
    public PageResult<PublicityVO> page(long pageNum, long pageSize, String type, Long orgId,
                                        String status) {
        LambdaQueryWrapper<BizPublicity> qw = new LambdaQueryWrapper<BizPublicity>()
                .eq(type != null && !type.isBlank(), BizPublicity::getPublicityType, type)
                .eq(orgId != null, BizPublicity::getOrgId, orgId)
                .eq(status != null && !status.isBlank(), BizPublicity::getPublicityStatus, status)
                .orderByDesc(BizPublicity::getId);
        applyPublicityScope(qw);
        IPage<BizPublicity> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<PublicityVO> rows = page.getRecords().stream().map(PublicityVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    /**
     * 公示的数据范围。
     *
     * <p>公示属于对公众公开的信息（中签名单本身已脱敏），因此「仅本人」角色
     * 也能查看已发布/已结束的公示，但看不到草稿。
     */
    private void applyPublicityScope(LambdaQueryWrapper<BizPublicity> qw) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.in(BizPublicity::getPublicityStatus,
                    java.util.List.of(PublicityStatus.PUBLISHED.name(),
                            PublicityStatus.CLOSED.name()));
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(BizPublicity::getOrgId, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(BizPublicity::getOrgId, scope.orgId());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PublicityVO publish(Long id) {
        BizPublicity e = require(id);
        transition(e, PublicityStatus.PUBLISHED);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return PublicityVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PublicityVO close(Long id, String remark) {
        BizPublicity e = require(id);
        transition(e, PublicityStatus.CLOSED);
        // 提前结束配租公示视为不合规，记录警告（仍允许关闭，由人工判断特殊情况）
        if (PublicityType.ALLOCATION.name().equals(e.getPublicityType())
                && e.getEndDate() != null && LocalDate.now().isBefore(e.getEndDate())) {
            log.warn("⚠️ 配租公示 {} 提前结束（应公示至 {}），请确认是否合规",
                    e.getPublicityNo(), e.getEndDate());
        }
        if (remark != null && !remark.isBlank()) {
            e.setContent((e.getContent() == null ? "" : e.getContent() + "\n") + remark);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return PublicityVO.from(e);
    }

    @Override
    public boolean hasCompletedAllocationPublicity(Long orgId, LocalDate referenceDate) {
        Long n = mapper.selectCount(new LambdaQueryWrapper<BizPublicity>()
                .eq(BizPublicity::getPublicityType, PublicityType.ALLOCATION.name())
                .eq(BizPublicity::getPublicityStatus, PublicityStatus.CLOSED.name())
                .eq(orgId != null, BizPublicity::getOrgId, orgId));
        return n != null && n > 0;
    }

    // ==================== 内部 ====================

    private BizPublicity require(Long id) {
        BizPublicity e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("公示");
        }
        return e;
    }

    private static void transition(BizPublicity e, PublicityStatus target) {
        PublicityStatus from;
        try {
            from = PublicityStatus.valueOf(e.getPublicityStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("公示状态非法: " + e.getPublicityStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!PublicityStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "公示状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setPublicityStatus(target.name());
    }

    @Override
    public java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO> winners(Long publicityId) {
        com.yundao.bp.biz.entity.BizPublicity p = mapper.selectById(publicityId);
        if (p == null || p.getBatchId() == null) {
            return java.util.List.of();
        }
        java.util.List<com.yundao.bp.biz.entity.BizLotteryResult> results =
                winnerLotteryMapper.selectList(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.biz.entity.BizLotteryResult>()
                                .eq(com.yundao.bp.biz.entity.BizLotteryResult::getBatchId,
                                        p.getBatchId())
                                .orderByAsc(com.yundao.bp.biz.entity.BizLotteryResult::getLotterySeq));
        if (results.isEmpty()) {
            return java.util.List.of();
        }
        java.util.Set<Long> personIds = new java.util.HashSet<>();
        java.util.Set<Long> houseIds = new java.util.HashSet<>();
        for (com.yundao.bp.biz.entity.BizLotteryResult r : results) {
            if (r.getPersonId() != null) {
                personIds.add(r.getPersonId());
            }
            if (r.getHouseId() != null) {
                houseIds.add(r.getHouseId());
            }
        }
        java.util.Map<Long, com.yundao.bp.person.entity.Person> persons = new java.util.HashMap<>();
        if (!personIds.isEmpty()) {
            for (com.yundao.bp.person.entity.Person person
                    : winnerPersonMapper.selectBatchIds(personIds)) {
                persons.put(person.getId(), person);
            }
        }
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetHouse> houses = new java.util.HashMap<>();
        if (!houseIds.isEmpty()) {
            for (com.yundao.bp.asset.entity.AssetHouse house
                    : winnerHouseMapper.selectBatchIds(houseIds)) {
                houses.put(house.getId(), house);
            }
        }
        java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO> out = new java.util.ArrayList<>();
        for (com.yundao.bp.biz.entity.BizLotteryResult r : results) {
            com.yundao.bp.person.entity.Person person = persons.get(r.getPersonId());
            com.yundao.bp.asset.entity.AssetHouse house = houses.get(r.getHouseId());
            String type = r.getResultType();
            String typeLabel = "WIN".equals(type) ? "中签"
                    : ("WAIT".equals(type) || "BACKUP".equals(type) ? "候补" : "未中签");
            out.add(new com.yundao.bp.biz.dto.PublicityWinnerVO(
                    r.getPersonId(),
                    r.getHouseId(),
                    person == null ? null : person.getRealName(),
                    person == null ? null : person.getIdCardMask(),
                    maskPhone(person == null ? null : person.getPhone()),
                    house == null ? null : house.getHouseName(),
                    r.getLotterySeq(),
                    r.getSelectSeq(),
                    type,
                    typeLabel));
        }
        return out;
    }

    /** 手机号脱敏：139****0000 */
    private String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4);
    }
}
