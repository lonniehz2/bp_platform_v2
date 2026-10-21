package com.yundao.bp.common.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.BlockAttackInnerInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.TenantLineInnerInterceptor;
import com.baomidou.mybatisplus.extension.plugins.handler.TenantLineHandler;
import com.yundao.bp.common.tenant.TenantContext;
import java.util.Set;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.expression.StringValue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis-Plus 插件配置：多租户行级隔离 + 分页 + 防全表更新。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §19（行级隔离）。
 *
 * <p><b>忽略清单纪律</b>（违反即越权）：
 * <ol>
 *   <li>只放<b>真正全局</b>的表（字典、权限资源、开放接口清单、系统内置模板）</li>
 *   <li>新增忽略表<b>必须代码评审</b></li>
 *   <li>清单与 {@code TenantIgnoreTablesTest} 单测联动，改动会被测试发现</li>
 * </ol>
 */
@Configuration
public class MybatisTenantConfig {

    /**
     * 无需租户隔离的表（表名不带反引号）。
     *
     * <p>注意：{@code bp_iam_tenant} 是租户主表本身，它<b>没有 tenant_id 列</b>，故必须忽略。
     */
    public static final Set<String> IGNORE_TABLES = Set.of(
            "bp_iam_tenant",        // 租户主表本身
            "bp_iam_permission",    // 全局权限资源定义
            "bp_sys_dict",          // 系统内置字典
            "bp_sys_config",        // 系统参数（全局默认 + 租户覆盖，由 ConfigService 自行合并，不能加租户过滤）
            "bp_msg_template",      // 系统内置消息模板
            "bp_rpt_report_def",    // 报表定义（全局默认 + 租户覆盖）
            "bp_rpt_screen_def",    // 大屏定义（全局默认 + 租户覆盖）
            "bp_open_api",          // 开放接口清单
            // 调用日志按 appKey 归属，表本身无 tenant_id 列；
            // 若不忽略，租户插件会给 INSERT 注入 tenant_id 导致写入失败
            "bp_open_call_log"
    );

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();

        // 1) 多租户：必须放在分页之前
        interceptor.addInnerInterceptor(new TenantLineInnerInterceptor(tenantLineHandler()));

        // 2) 分页
        PaginationInnerInterceptor pagination = new PaginationInnerInterceptor(DbType.MYSQL);
        pagination.setMaxLimit(500L);          // 与 IoT 分页上限一致，防超大页
        pagination.setOverflow(false);
        interceptor.addInnerInterceptor(pagination);

        // 3) 防全表更新/删除（只允许带 where 的 update/delete）
        interceptor.addInnerInterceptor(new BlockAttackInnerInterceptor());

        return interceptor;
    }

    private TenantLineHandler tenantLineHandler() {
        return new TenantLineHandler() {
            @Override
            public Expression getTenantId() {
                // ★ 上下文缺失时 TenantContext.tenantId() 直接抛异常，
                //   绝不会退化为“查全租户”
                return new StringValue(TenantContext.tenantId());
            }

            @Override
            public String getTenantIdColumn() {
                return "tenant_id";
            }

            @Override
            public boolean ignoreTable(String tableName) {
                return IGNORE_TABLES.contains(tableName);
            }
        };
    }
}
