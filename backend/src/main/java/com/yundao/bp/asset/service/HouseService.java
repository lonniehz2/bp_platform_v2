package com.yundao.bp.asset.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.HouseVO;

/**
 * 房源服务。
 */
public interface HouseService {

    /**
     * 创建房源。
     *
     * <p>自动完成：校验挂载节点（仅 ROOM/BED）、派生 orgId、同组织编码唯一、
     * 初始状态 {@code PENDING_ALLOC}、已入住人数 0。
     */
    HouseVO create(HouseCreateCmd cmd);

    HouseVO get(Long id);

    PageResult<HouseVO> page(long pageNum, long pageSize, Long orgId,
                             Long spaceId, String houseStatus, String houseType, String keyword,
                             Boolean includeChildren);

    HouseVO changeStatus(Long id, String targetStatus);

    /** 批量导入房源（CSV）。 */
    java.util.Map<String, Object> importCsv(
            org.springframework.web.multipart.MultipartFile file);

    /** 为房间批量生成床位房源，返回新建数量。 */
    int batchCreateBeds(Long roomSpaceId, int count,
                        java.math.BigDecimal rentStandard, java.math.BigDecimal areaPerBed);

    /** 房间下的床位列表（含租住状态与在租人）。 */
    java.util.List<java.util.Map<String, Object>> listBeds(Long roomSpaceId);
}
