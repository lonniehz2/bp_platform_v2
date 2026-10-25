package com.yundao.bp.sys.service;

import com.yundao.bp.sys.entity.SysDict;
import java.util.List;
import java.util.Map;

/**
 * 数据字典服务。
 *
 * <p>租户级优先：同 `dict_type + dict_code` 时，本租户配置覆盖系统内置。
 */
public interface DictService {

    /** 按类型取字典项（租户优先，已排序）。 */
    List<SysDict> listByType(String dictType);

    /** 按类型取「编码 → 标签」映射（前端下拉用）。 */
    Map<String, String> mapByType(String dictType);

    /** 取某类型某编码的标签。 */
    String label(String dictType, String dictCode);

    /** 全部字典类型列表。 */
    List<String> types();

    /** 新增字典项。 */
    SysDict create(String dictType, String dictCode, String dictLabel, String dictValue,
                   Integer sortNo, String remark);

    /** 启用/停用。 */
    SysDict setStatus(Long id, boolean enabled);

    /** 按类型取字典项；includeDisabled=true 时含已停用（管理页）。 */
    java.util.List<com.yundao.bp.sys.entity.SysDict> listByType(String dictType,
                                                               boolean includeDisabled);
}
