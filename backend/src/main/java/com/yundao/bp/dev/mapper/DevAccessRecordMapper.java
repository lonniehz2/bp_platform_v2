package com.yundao.bp.dev.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.dev.entity.DevAccessRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DevAccessRecordMapper extends BaseMapper<DevAccessRecord> {

    /**
     * 今日通行统计（一次查询返回总数与异常数，避免两次全表扫描）。
     *
     * @return 第 0 位为总数，第 1 位为异常数
     */
    @org.apache.ibatis.annotations.Select("""
            <script>
            select count(*) as total,
                   sum(case when is_abnormal = 1 then 1 else 0 end) as abnormal
            from bp_dev_access_record
            where tenant_id = #{tenantId}
              and open_time &gt;= #{startOfDay}
              <if test="orgId != null"> and org_id = #{orgId} </if>
            </script>
            """)
    java.util.Map<String, Object> countTodayPair(
            @org.apache.ibatis.annotations.Param("tenantId") String tenantId,
            @org.apache.ibatis.annotations.Param("orgId") Long orgId,
            @org.apache.ibatis.annotations.Param("startOfDay") java.time.LocalDateTime startOfDay);
}
