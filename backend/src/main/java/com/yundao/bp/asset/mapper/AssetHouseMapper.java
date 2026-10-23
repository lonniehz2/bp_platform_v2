package com.yundao.bp.asset.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.asset.entity.AssetHouse;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AssetHouseMapper extends BaseMapper<AssetHouse> {

    /**
     * 行级排他锁：返回主键即代表当前事务已持有该行锁。
     *
     * <p>用于跨实例并发保护（JVM 锁只在单实例有效）。必须在事务内调用。
     */
    @org.apache.ibatis.annotations.Select("select id from bp_asset_house where id = #{id} for update")
    Long lockForUpdate(@org.apache.ibatis.annotations.Param("id") Long id);
}
