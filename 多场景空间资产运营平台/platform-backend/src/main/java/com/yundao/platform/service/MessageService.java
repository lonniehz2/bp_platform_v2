package com.yundao.platform.service;

import com.yundao.platform.common.auth.UserContext;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class MessageService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public MessageService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list() {
        UserContext.Principal principal = UserContext.require();
        return jdbc.queryForList(
                "select id, title, content, biz_type bizType, biz_id bizId, read_status readStatus, create_time createTime "
                        + "from bp_message where tenant_id=? and is_deleted=0 "
                        + "and (user_id is null or user_id=?) order by id desc limit 200",
                principal.tenantId(), principal.userId());
    }

    public Map<String, Object> create(CreateCmd cmd) {
        UserContext.Principal principal = UserContext.require();
        if (cmd.title() == null || cmd.title().isBlank()) {
            throw BizException.param("消息标题不能为空");
        }
        long id = idGen.nextId();
        jdbc.update("insert into bp_message(id,tenant_id,user_id,title,content,biz_type,biz_id,"
                        + "read_status,is_deleted) values(?,?,?,?,?,?,?, 'UNREAD',0)",
                id, principal.tenantId(), cmd.userId(), cmd.title().trim(), cmd.content(),
                cmd.bizType(), cmd.bizId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("readStatus", "UNREAD");
        return out;
    }

    public Map<String, Object> read(long id) {
        UserContext.Principal principal = UserContext.require();
        long updated = jdbc.update("update bp_message set read_status='READ' "
                        + "where id=? and tenant_id=? and (user_id is null or user_id=?) and is_deleted=0",
                id, principal.tenantId(), principal.userId());
        if (updated == 0) {
            throw BizException.notFound("消息不存在");
        }
        return Map.of("id", id, "readStatus", "READ");
    }

    public Map<String, Object> readAll() {
        UserContext.Principal principal = UserContext.require();
        int count = jdbc.update("update bp_message set read_status='READ' "
                        + "where tenant_id=? and (user_id is null or user_id=?) and read_status='UNREAD' and is_deleted=0",
                principal.tenantId(), principal.userId());
        return Map.of("updated", count);
    }

    public record CreateCmd(Long userId, String title, String content, String bizType, String bizId) {
    }
}
