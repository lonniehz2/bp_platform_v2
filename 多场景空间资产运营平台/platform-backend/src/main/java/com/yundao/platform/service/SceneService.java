package com.yundao.platform.service;

import com.yundao.platform.common.tenant.TenantContext;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class SceneService {

    private final JdbcTemplate jdbc;

    public SceneService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> scenes() {
        return jdbc.queryForList(
                "select s.scene_code sceneCode, s.scene_name sceneName, s.sort_no sortNo, "
                        + "case when ts.id is null then 0 else 1 end enabled "
                        + "from bp_scene_profile s left join bp_tenant_scene ts "
                        + "on ts.tenant_id=? and ts.scene_code=s.scene_code and ts.status='ENABLED' "
                        + "where s.status='ENABLED' order by s.sort_no, s.scene_code",
                TenantContext.require());
    }

    public List<Map<String, Object>> businessModes(String sceneCode) {
        return jdbc.queryForList(
                "select mode_code modeCode, mode_name modeName, sort_no sortNo "
                        + "from bp_business_mode where scene_code=? and status='ENABLED' "
                        + "order by sort_no, mode_code",
                sceneCode);
    }
}
