package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.InspectionPlanCmd;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import java.util.Map;

/** 巡检计划服务。 */
public interface InspectionPlanService {

    OpsInspectionPlan create(InspectionPlanCmd cmd);

    PageResult<OpsInspectionPlan> page(long pageNum, long pageSize, String planStatus);

    /** 执行到期计划：生成工单并推进下次执行日，返回 {generated, skipped}。 */
    Map<String, Object> runDue();
}
