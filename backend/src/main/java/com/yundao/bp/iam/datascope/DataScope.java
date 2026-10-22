package com.yundao.bp.iam.datascope;

import java.util.List;

/**
 * 当前登录用户的数据范围。
 *
 * @param level   ALL / ORG_SUB / ORG / SELF
 * @param orgId   用户所属组织（ORG/ORG_SUB 时用于过滤）
 * @param orgIds  ORG_SUB 时预先展开的组织 ID 列表（空表示未展开）
 * @param personId 用户绑定的人员 ID（SELF 时用于过滤）
 */
public record DataScope(String level, Long orgId, List<Long> orgIds, Long personId) {

    public boolean isAll() {
        return "ALL".equals(level);
    }

    public boolean isSelf() {
        return "SELF".equals(level);
    }
}
