package com.yundao.bp.iam.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.iam.dto.OperatorLoginCmd;
import com.yundao.bp.iam.dto.OperatorLoginVO;
import com.yundao.bp.iam.entity.PlatformOperator;
import com.yundao.bp.iam.entity.PlatformOperatorSession;
import com.yundao.bp.iam.mapper.PlatformOperatorMapper;
import com.yundao.bp.iam.mapper.PlatformOperatorSessionMapper;
import com.yundao.bp.iam.security.PasswordHasher;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import java.time.LocalDateTime;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 平台运营超管登录与令牌。 */
@Service
public class PlatformOperatorService {

    private static final Logger log = LoggerFactory.getLogger(PlatformOperatorService.class);

    private final PlatformOperatorMapper operatorMapper;
    private final PlatformOperatorSessionMapper sessionMapper;
    private final PasswordHasher hasher;
    private final SnowflakeIdGenerator idGen;

    public PlatformOperatorService(PlatformOperatorMapper operatorMapper,
                                   PlatformOperatorSessionMapper sessionMapper,
                                   PasswordHasher hasher,
                                   SnowflakeIdGenerator idGen) {
        this.operatorMapper = operatorMapper;
        this.sessionMapper = sessionMapper;
        this.hasher = hasher;
        this.idGen = idGen;
    }

    @Transactional(rollbackFor = Exception.class)
    public OperatorLoginVO login(OperatorLoginCmd cmd, String ip) {
        PlatformOperator op = operatorMapper.selectOne(new LambdaQueryWrapper<PlatformOperator>()
                .eq(PlatformOperator::getUsername, cmd.username())
                .eq(PlatformOperator::getIsDeleted, 0)
                .last("LIMIT 1"));
        if (op == null) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "账号或密码错误");
        }
        if (!"ENABLED".equals(op.getStatus())) {
            throw new BizException(ErrorCode.FORBIDDEN, "账号已停用");
        }
        if (op.getLockedUntil() != null && op.getLockedUntil().isAfter(LocalDateTime.now())) {
            throw new BizException(ErrorCode.FORBIDDEN,
                    "登录失败次数过多，请于 " + op.getLockedUntil() + " 后重试");
        }
        if (!hasher.verify(cmd.password(), op.getPasswordHash())) {
            int fail = (op.getFailCount() == null ? 0 : op.getFailCount()) + 1;
            op.setFailCount(fail);
            if (fail >= 5) {
                op.setLockedUntil(LocalDateTime.now().plusMinutes(15));
            }
            op.setUpdateTime(LocalDateTime.now());
            operatorMapper.updateById(op);
            throw new BizException(ErrorCode.UNAUTHORIZED, "账号或密码错误");
        }
        op.setFailCount(0);
        op.setLockedUntil(null);
        op.setLastLoginTime(LocalDateTime.now());
        op.setUpdateTime(LocalDateTime.now());
        operatorMapper.updateById(op);

        String token = UUID.randomUUID().toString().replace("-", "");
        PlatformOperatorSession s = new PlatformOperatorSession();
        s.setId(idGen.nextId());
        s.setOperatorId(op.getId());
        s.setToken(token);
        s.setStatus("ACTIVE");
        s.setExpireTime(LocalDateTime.now().plusHours(12));
        s.setCreateTime(LocalDateTime.now());
        sessionMapper.insert(s);
        log.info("运营超管登录：{} ip={}", op.getUsername(), ip);
        return new OperatorLoginVO(token, op.getId(), op.getUsername(), op.getRealName(),
                op.getMustChangePassword() != null && op.getMustChangePassword() == 1);
    }

    /** 校验令牌；无效抛出 401。 */
    public PlatformOperator require(String token) {
        if (token == null || token.isBlank()) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "请先登录运营台");
        }
        PlatformOperatorSession s = sessionMapper.selectOne(
                new LambdaQueryWrapper<PlatformOperatorSession>()
                        .eq(PlatformOperatorSession::getToken, token)
                        .eq(PlatformOperatorSession::getStatus, "ACTIVE")
                        .last("LIMIT 1"));
        if (s == null || s.getExpireTime().isBefore(LocalDateTime.now())) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "登录已过期，请重新登录");
        }
        PlatformOperator op = operatorMapper.selectById(s.getOperatorId());
        if (op == null || !"ENABLED".equals(op.getStatus())
                || (op.getIsDeleted() != null && op.getIsDeleted() == 1)) {
            throw new BizException(ErrorCode.UNAUTHORIZED, "账号不可用");
        }
        return op;
    }

    @Transactional(rollbackFor = Exception.class)
    public void changePassword(String token, String oldPassword, String newPassword) {
        PlatformOperator op = require(token);
        if (!hasher.verify(oldPassword, op.getPasswordHash())) {
            throw new BizException(ErrorCode.PARAM_INVALID, "原密码不正确");
        }
        if (newPassword == null || newPassword.length() < 10) {
            throw new BizException(ErrorCode.PARAM_INVALID, "新密码至少 10 位");
        }
        op.setPasswordHash(hasher.hash(newPassword));
        op.setMustChangePassword(0);
        op.setUpdateTime(LocalDateTime.now());
        operatorMapper.updateById(op);
    }

    @Transactional(rollbackFor = Exception.class)
    public void logout(String token) {
        if (token == null || token.isBlank()) {
            return;
        }
        PlatformOperatorSession s = sessionMapper.selectOne(
                new LambdaQueryWrapper<PlatformOperatorSession>()
                        .eq(PlatformOperatorSession::getToken, token)
                        .last("LIMIT 1"));
        if (s != null) {
            s.setStatus("LOGOUT");
            sessionMapper.updateById(s);
        }
    }
}
