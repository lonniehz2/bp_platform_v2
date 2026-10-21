package com.yundao.bp.asset.service;

import com.yundao.bp.asset.dto.SpaceCreateCmd;
import com.yundao.bp.asset.dto.SpaceVO;
import java.util.List;

/**
 * 空间树服务。
 */
public interface SpaceService {

    /** 创建节点（自动生成 space_path / path_code / space_level / full_name，并校验父子类型）。 */
    SpaceVO create(SpaceCreateCmd cmd);

    SpaceVO get(Long id);

    /** 查询直接下级。 */
    List<SpaceVO> children(Long parentId);

    /** 查询整棵子树（按 path_code 前缀，天然有序）。 */
    List<SpaceVO> subtree(Long rootId);

    /** 查询某组织下的树（顶级 + 递归）。 */
    List<SpaceVO> treeOfOrg(Long orgId);

    void delete(Long id);
}
