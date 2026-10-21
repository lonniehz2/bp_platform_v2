package com.yundao.bp.msg.service;

import com.yundao.bp.msg.dto.TodoOverviewVO;

/**
 * 统一待办中心：把散落在各模块的「待办」聚合成一个入口。
 */
public interface TodoCenterService {

    /** 各模块待办计数（按当前租户）。 */
    TodoOverviewVO overview();
}
