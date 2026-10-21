package com.yundao.bp.asset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.constant.HouseStatus;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.SpaceOccupancy;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.SpaceOccupancyMapper;
import com.yundao.bp.asset.service.OccupancyService;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 房源占用服务实现。
 *
 * <p><b>设计要点</b>：
 * <ol>
 *   <li>占用流水（{@code bp_asset_space_occupancy}）与房源状态
 *       （{@code bp_asset_house.house_status}）同事务更新，二者不会打架</li>
 *   <li>房源状态不走「直接赋值」，而是用 {@link HouseStatus#nextOf} 求一条
 *       合法路径（如 空置→锁定→已配租→已入住），非法跳转直接拒绝</li>
 *   <li>合租房源允许多条 ACTIVE 占用；只有「无任何 ACTIVE」时才释放为空置</li>
 *   <li>以 {@code (source_type, source_id, ACTIVE)} 做幂等键，重复调用不产生脏数据</li>
 * </ol>
 */
@Service
public class OccupancyServiceImpl implements OccupancyService {

    private static final Logger log = LoggerFactory.getLogger(OccupancyServiceImpl.class);

    private static final String SOURCE_CONTRACT = "CONTRACT";
    private static final String OCCUPY_CONTRACT = "CONTRACT";
    private static final String STATUS_ACTIVE = "ACTIVE";
    private static final String STATUS_FINISHED = "FINISHED";

    private final SpaceOccupancyMapper occupancyMapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;

    public OccupancyServiceImpl(SpaceOccupancyMapper occupancyMapper,
                                AssetHouseMapper houseMapper,
                                SnowflakeIdGenerator idGen) {
        this.occupancyMapper = occupancyMapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void occupyByContract(Long contractId, Long houseId, Long spaceId, Long personId,
                                 LocalDate start, LocalDate end) {
        if (houseId == null) {
            throw BizException.paramInvalid("房源不能为空，无法建立占用");
        }
        SpaceOccupancy active = findActive(contractId);
        if (active != null) {
            // 幂等：已占用过，只同步租期
            active.setStartDate(start == null ? active.getStartDate() : start);
            active.setEndDate(end);
            occupancyMapper.updateById(active);
            return;
        }

        AssetHouse house = houseMapper.selectById(houseId);
        if (house == null) {
            throw BizException.notFound("房源");
        }
        int max = house.getMaxCapacity() == null ? 0 : house.getMaxCapacity();
        int cur = house.getCurrentCapacity() == null ? 0 : house.getCurrentCapacity();
        if (max > 0 && cur >= max) {
            throw BizException.stateConflict(
                    "房源已满员（已住 " + cur + " / 上限 " + max + "），不能重复配租");
        }

        SpaceOccupancy o = new SpaceOccupancy();
        o.setId(idGen.nextId());
        o.setTenantId(TenantContext.tenantId());
        Long effectiveSpaceId = spaceId != null ? spaceId : house.getSpaceId();
        if (effectiveSpaceId == null) {
            throw BizException.paramInvalid("房源缺少空间归属，无法建立占用");
        }
        o.setSpaceId(effectiveSpaceId);
        o.setHouseId(houseId);
        o.setPersonId(personId);
        o.setOccupyType(OCCUPY_CONTRACT);
        o.setIsPrimary(1);
        o.setStartDate(start != null ? start : LocalDate.now());
        o.setEndDate(end);
        o.setStatus(STATUS_ACTIVE);
        o.setSourceType(SOURCE_CONTRACT);
        o.setSourceId(contractId);
        occupancyMapper.insert(o);

        transit(house, HouseStatus.OCCUPIED);
        house.setCurrentCapacity(cur + 1);
        houseMapper.updateById(house);

        log.info("合同 {} 占房成功：房源 {}，租期 {} ~ {}，当前入住 {}/{}",
                contractId, houseId, o.getStartDate(), end, cur + 1, max);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void releaseByContract(Long contractId, LocalDate actualEnd) {
        List<SpaceOccupancy> actives = occupancyMapper.selectList(
                new LambdaQueryWrapper<SpaceOccupancy>()
                        .eq(SpaceOccupancy::getSourceType, SOURCE_CONTRACT)
                        .eq(SpaceOccupancy::getSourceId, contractId)
                        .eq(SpaceOccupancy::getStatus, STATUS_ACTIVE));
        if (actives.isEmpty()) {
            return; // 幂等：本来就没占房（草稿合同取消等）
        }
        LocalDate end = actualEnd != null ? actualEnd : LocalDate.now();
        for (SpaceOccupancy o : actives) {
            o.setStatus(STATUS_FINISHED);
            o.setEndDate(end);
            occupancyMapper.updateById(o);
        }

        Long houseId = actives.get(0).getHouseId();
        AssetHouse house = houseId == null ? null : houseMapper.selectById(houseId);
        if (house == null) {
            return;
        }
        int cur = house.getCurrentCapacity() == null ? 0 : house.getCurrentCapacity();
        int left = Math.max(0, cur - actives.size());
        house.setCurrentCapacity(left);
        long remaining = occupancyMapper.selectCount(
                new LambdaQueryWrapper<SpaceOccupancy>()
                        .eq(SpaceOccupancy::getHouseId, houseId)
                        .eq(SpaceOccupancy::getStatus, STATUS_ACTIVE));
        if (remaining == 0) {
            // 没有其它在用占用，房源回到空置
            transit(house, HouseStatus.VACANT);
        }
        houseMapper.updateById(house);
        log.info("合同 {} 退房：房源 {} 释放 {} 条占用，当前入住 {}", contractId, houseId, actives.size(), left);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void extendByContract(Long contractId, LocalDate newEnd) {
        SpaceOccupancy active = findActive(contractId);
        if (active == null || newEnd == null) {
            return;
        }
        active.setEndDate(newEnd);
        occupancyMapper.updateById(active);
        log.info("合同 {} 续签：占用结束日延长至 {}", contractId, newEnd);
    }

    private SpaceOccupancy findActive(Long contractId) {
        return occupancyMapper.selectOne(new LambdaQueryWrapper<SpaceOccupancy>()
                .eq(SpaceOccupancy::getSourceType, SOURCE_CONTRACT)
                .eq(SpaceOccupancy::getSourceId, contractId)
                .eq(SpaceOccupancy::getStatus, STATUS_ACTIVE)
                .last("LIMIT 1"));
    }

    /**
     * 按状态机把房源推进到目标状态。
     *
     * <p>不直接赋值，而是先求一条合法路径；路径不存在说明业务上不该发生
     * （例如从「停用」直接跳到「已入住」），直接拒绝，避免把脏状态写进库。
     */
    private void transit(AssetHouse house, HouseStatus target) {
        HouseStatus from;
        try {
            from = HouseStatus.valueOf(house.getHouseStatus());
        } catch (RuntimeException ex) {
            from = HouseStatus.VACANT; // 历史空值按空置处理
        }
        if (from == target) {
            return;
        }
        List<HouseStatus> path = shortestPath(from, target);
        if (path.isEmpty()) {
            throw BizException.stateConflict(
                    "房源状态不允许从「" + from.label() + "」变为「" + target.label() + "」");
        }
        house.setHouseStatus(target.name());
        house.setLockStatusTime(java.time.LocalDateTime.now());
        if (path.size() > 2) {
            log.info("房源 {} 状态 {} → {}（经由 {}）", house.getId(), from.label(), target.label(),
                    path.subList(1, path.size() - 1));
        }
    }

    /** 在状态机图上求最短路径；不可达返回空列表。 */
    private static List<HouseStatus> shortestPath(HouseStatus from, HouseStatus to) {
        Map<HouseStatus, HouseStatus> prev = new HashMap<>();
        Deque<HouseStatus> queue = new ArrayDeque<>();
        queue.add(from);
        prev.put(from, null);
        while (!queue.isEmpty()) {
            HouseStatus cur = queue.poll();
            if (cur == to) {
                List<HouseStatus> path = new ArrayList<>();
                for (HouseStatus s = to; s != null; s = prev.get(s)) {
                    path.add(0, s);
                }
                return path;
            }
            for (HouseStatus next : HouseStatus.nextOf(cur)) {
                if (!prev.containsKey(next)) {
                    prev.put(next, cur);
                    queue.add(next);
                }
            }
        }
        return List.of();
    }
}
