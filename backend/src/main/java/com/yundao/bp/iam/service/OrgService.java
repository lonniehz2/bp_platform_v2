package com.yundao.bp.iam.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.iam.dto.OrgCreateCmd;
import com.yundao.bp.iam.dto.OrgVO;
import java.util.List;

/**
 * 组织服务。
 */
public interface OrgService {

    /** 创建组织（自动生成 ID、计算 org_path / org_level）。 */
    OrgVO create(OrgCreateCmd cmd);

    /** 按 ID 查询（租户插件自动限制在本租户内）。 */
    OrgVO get(Long id);

    /** 分页查询。 */
    PageResult<OrgVO> page(long pageNum, long pageSize, String keyword,
                            Long parentId, Boolean includeSubtree);

    /** 查询子组织（直接下级）。 */
    List<OrgVO> children(Long parentId);

    /** 逻辑删除。 */
    void delete(Long id);
}
