package com.yundao.platform.config;

import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.service.AuthService;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class DataInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);
    private static final String TENANT = "350600";

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final AuthService authService;

    public DataInitializer(JdbcTemplate jdbc, IdGenerator idGen, AuthService authService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.authService = authService;
    }

    @Override
    public void run(String... args) {
        Long users = jdbc.queryForObject(
                "select count(*) from bp_user where tenant_id=? and username='admin'", Long.class, TENANT);
        if (users != null && users > 0) {
            return;
        }
        long userId = idGen.nextId();
        jdbc.update("insert into bp_user(id,tenant_id,username,password_hash,display_name,user_status,is_deleted) "
                        + "values(?,?,?,?,?,'ENABLED',0)",
                userId, TENANT, "admin", authService.encode("admin123"), "平台管理员");
        List<Long> roleIds = jdbc.queryForList(
                "select id from bp_role where tenant_id=? and scene_code='GUARANTEE' "
                        + "and role_code='GUARANTEE_ADMIN'", Long.class, TENANT);
        long roleId;
        if (roleIds.isEmpty()) {
            roleId = idGen.nextId();
            jdbc.update("insert into bp_role(id,tenant_id,scene_code,role_code,role_name,role_status) "
                            + "values(?,?,'GUARANTEE','GUARANTEE_ADMIN','保障房管理员','ENABLED')",
                    roleId, TENANT);
        } else {
            roleId = roleIds.get(0);
        }
        jdbc.update("insert ignore into bp_user_role(id,tenant_id,user_id,role_id) values(?,?,?,?)",
                idGen.nextId(), TENANT, userId, roleId);
        log.info("已初始化平台管理员 admin/admin123");
    }
}
