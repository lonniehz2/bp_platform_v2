package com.yundao.bp.common.id;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 雪花 ID 生成器装配。workerId / datacenterId 由部署环境注入，避免多实例冲突。
 */
@Configuration
public class IdConfig {

    @Bean
    public SnowflakeIdGenerator snowflakeIdGenerator(
            @Value("${bp.snowflake.datacenter-id:1}") long datacenterId,
            @Value("${bp.snowflake.worker-id:1}") long workerId) {
        return new SnowflakeIdGenerator(datacenterId, workerId);
    }
}
