package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.IamOrg;
import org.apache.ibatis.annotations.Mapper;

/**
 * 组织 Mapper。
 *
 * <p>⚠️ 所有 SQL <b>不要手写 tenant_id 条件</b>——由租户插件自动追加，
 * 手写反而会重复。唯一例外是需要跨租户的场景（应为极少数且需评审）。
 */
@Mapper
public interface IamOrgMapper extends BaseMapper<IamOrg> {
}
