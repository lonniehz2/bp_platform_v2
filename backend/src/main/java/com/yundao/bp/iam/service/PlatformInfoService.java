package com.yundao.bp.iam.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.dto.PlatformInfoUpdateCmd;
import com.yundao.bp.iam.dto.PlatformInfoVO;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import java.time.LocalDateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 平台信息维护：只允许改名称/类型/区域/状态，编码不可变。 */
@Service
public class PlatformInfoService {

    private static final Logger log = LoggerFactory.getLogger(PlatformInfoService.class);

    private final IamTenantMapper tenantMapper;

    public PlatformInfoService(IamTenantMapper tenantMapper) {
        this.tenantMapper = tenantMapper;
    }

    public PlatformInfoVO get() {
        return PlatformInfoVO.from(requireCurrent());
    }

    @Transactional(rollbackFor = Exception.class)
    public PlatformInfoVO update(PlatformInfoUpdateCmd cmd) {
        IamTenant t = requireCurrent();
        String before = t.getTenantName() + "/" + t.getTenantType() + "/" + t.getRegionCode()
                + "/" + t.getStatus();
        t.setTenantName(cmd.tenantName());
        if (cmd.tenantType() != null && !cmd.tenantType().isBlank()) {
            t.setTenantType(cmd.tenantType());
        }
        t.setRegionCode(cmd.regionCode());
        if (cmd.status() != null && !cmd.status().isBlank()) {
            t.setStatus(cmd.status());
        }
        t.setUpdateTime(LocalDateTime.now());
        tenantMapper.updateById(t);
        log.info("平台信息修改：{} -> {}/{}/{}/{}", before, t.getTenantName(), t.getTenantType(),
                t.getRegionCode(), t.getStatus());
        return PlatformInfoVO.from(t);
    }

    private IamTenant requireCurrent() {
        String code = TenantContext.tenantId();
        IamTenant t = tenantMapper.selectOne(new LambdaQueryWrapper<IamTenant>()
                .eq(IamTenant::getTenantCode, code)
                .last("LIMIT 1"));
        if (t == null) {
            throw BizException.notFound("平台信息");
        }
        return t;
    }
}
