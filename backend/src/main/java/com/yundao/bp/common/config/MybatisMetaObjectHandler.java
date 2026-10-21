package com.yundao.bp.common.config;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDateTime;
import org.apache.ibatis.reflection.MetaObject;
import org.springframework.stereotype.Component;

/**
 * 审计字段自动填充。
 *
 * <p>填充 {@code create_by / create_time / update_by / update_time}；
 * 操作人从租户上下文取，缺失时记为 {@code system}（系统任务/回调场景）。
 */
@Component
public class MybatisMetaObjectHandler implements MetaObjectHandler {

    private static final String SYSTEM = "system";

    @Override
    public void insertFill(MetaObject metaObject) {
        LocalDateTime now = LocalDateTime.now();
        String op = operator();
        strictInsertFill(metaObject, "createTime", LocalDateTime.class, now);
        strictInsertFill(metaObject, "updateTime", LocalDateTime.class, now);
        strictInsertFill(metaObject, "createBy", String.class, op);
        strictInsertFill(metaObject, "updateBy", String.class, op);
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
        strictUpdateFill(metaObject, "updateBy", String.class, operator());
    }

    private String operator() {
        Long uid = TenantContext.userId();
        return uid == null ? SYSTEM : String.valueOf(uid);
    }
}
