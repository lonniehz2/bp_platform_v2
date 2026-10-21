package com.yundao.bp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 云门道业务平台启动类。
 *
 * <p>模块边界（对应架构文档限界上下文）：
 * <pre>
 *  com.yundao.bp.common     通用（结果、异常、租户上下文、雪花ID、分页）
 *  com.yundao.bp.iam        BC-01 租户与权限
 *  com.yundao.bp.asset      BC-02 空间与资产
 *  com.yundao.bp.person     BC-03 人员与档案
 *  com.yundao.bp.grant      BC-04 权益与钥匙
 *  com.yundao.bp.biz        BC-05 业务办理（保障房闭环）
 *  com.yundao.bp.fin        BC-06 资金账务
 *  com.yundao.bp.iot        BC-07 设备与通信（防腐层，含签名协议）
 *  com.yundao.bp.ops        BC-08 告警与工单
 * </pre>
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class BpApplication {

    public static void main(String[] args) {
        SpringApplication.run(BpApplication.class, args);
    }
}
