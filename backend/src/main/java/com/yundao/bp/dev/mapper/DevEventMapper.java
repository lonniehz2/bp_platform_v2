package com.yundao.bp.dev.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.dev.entity.DevEvent;
import org.apache.ibatis.annotations.Mapper;

/** 设备事件。 */
@Mapper
public interface DevEventMapper extends BaseMapper<DevEvent> {
}
