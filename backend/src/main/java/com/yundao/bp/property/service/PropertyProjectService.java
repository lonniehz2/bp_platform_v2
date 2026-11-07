package com.yundao.bp.property.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.dto.OrgCreateCmd;
import com.yundao.bp.iam.dto.OrgVO;
import com.yundao.bp.iam.service.OrgService;
import com.yundao.bp.property.entity.PropProjectConfig;
import com.yundao.bp.property.mapper.PropProjectConfigMapper;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业项目：组织仍使用 bp_iam_org，项目配置放 prop_project_config。 */
@Service
public class PropertyProjectService {

    private final PropProjectConfigMapper mapper;
    private final OrgService orgService;
    private final SnowflakeIdGenerator idGen;

    public PropertyProjectService(PropProjectConfigMapper mapper, OrgService orgService,
                                  SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.orgService = orgService;
        this.idGen = idGen;
    }

    public List<PropProjectConfig> list() {
        return mapper.selectList(new LambdaQueryWrapper<PropProjectConfig>()
                .eq(PropProjectConfig::getTenantId, TenantContext.tenantId())
                .orderByAsc(PropProjectConfig::getProjectName));
    }

    @Transactional(rollbackFor = Exception.class)
    public PropProjectConfig create(CreateCmd cmd) {
        if (cmd.orgCode() == null || cmd.orgCode().isBlank()
                || cmd.orgName() == null || cmd.orgName().isBlank()) {
            throw BizException.paramInvalid("项目编码和名称不能为空");
        }
        Long dup = mapper.selectCount(new LambdaQueryWrapper<PropProjectConfig>()
                .eq(PropProjectConfig::getTenantId, TenantContext.tenantId())
                .eq(PropProjectConfig::getProjectCode, cmd.orgCode().trim()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("项目编码已存在");
        }
        OrgVO org = orgService.create(new OrgCreateCmd(
                cmd.orgCode().trim(), cmd.orgName().trim(), cmd.parentId(),
                "PROPERTY_PROJECT", null, null, null, null, null,
                cmd.address(), cmd.sortNo(), cmd.remark(),
                null, null, null, null, null));
        PropProjectConfig e = new PropProjectConfig();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setOrgId(org.id());
        e.setProjectCode(cmd.orgCode().trim());
        e.setProjectName(cmd.orgName().trim());
        e.setCompanyName(cmd.companyName());
        e.setContactName(cmd.contactName());
        e.setContactPhone(cmd.contactPhone());
        e.setServicePhone(cmd.servicePhone());
        e.setAddress(cmd.address());
        e.setReceiptHeader(cmd.receiptHeader() == null ? cmd.orgName().trim() : cmd.receiptHeader());
        e.setBankAccount(cmd.bankAccount());
        e.setStatus("ENABLED");
        e.setIsDeleted(0);
        e.setCreateBy(String.valueOf(TenantContext.userId()));
        e.setCreateTime(LocalDateTime.now());
        e.setUpdateBy(String.valueOf(TenantContext.userId()));
        e.setUpdateTime(LocalDateTime.now());
        mapper.insert(e);
        return e;
    }

    public PropProjectConfig update(Long orgId, UpdateCmd cmd) {
        PropProjectConfig e = require(orgId);
        if (cmd.projectName() != null && !cmd.projectName().isBlank()) {
            e.setProjectName(cmd.projectName().trim());
        }
        if (cmd.companyName() != null) e.setCompanyName(cmd.companyName());
        if (cmd.contactName() != null) e.setContactName(cmd.contactName());
        if (cmd.contactPhone() != null) e.setContactPhone(cmd.contactPhone());
        if (cmd.servicePhone() != null) e.setServicePhone(cmd.servicePhone());
        if (cmd.address() != null) e.setAddress(cmd.address());
        if (cmd.receiptHeader() != null) e.setReceiptHeader(cmd.receiptHeader());
        if (cmd.bankAccount() != null) e.setBankAccount(cmd.bankAccount());
        if (cmd.status() != null && !cmd.status().isBlank()) {
            if (!List.of("ENABLED", "DISABLED").contains(cmd.status())) {
                throw BizException.paramInvalid("项目状态不合法");
            }
            e.setStatus(cmd.status());
        }
        e.setUpdateBy(String.valueOf(TenantContext.userId()));
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return e;
    }

    private PropProjectConfig require(Long orgId) {
        PropProjectConfig e = mapper.selectOne(new LambdaQueryWrapper<PropProjectConfig>()
                .eq(PropProjectConfig::getTenantId, TenantContext.tenantId())
                .eq(PropProjectConfig::getOrgId, orgId)
                .last("LIMIT 1"));
        if (e == null) {
            throw BizException.notFound("物业项目");
        }
        return e;
    }

    public record CreateCmd(String orgCode, String orgName, Long parentId,
                            String companyName, String contactName, String contactPhone,
                            String servicePhone, String address, String receiptHeader,
                            String bankAccount, Integer sortNo, String remark) {
    }

    public record UpdateCmd(String projectName, String companyName, String contactName,
                            String contactPhone, String servicePhone, String address,
                            String receiptHeader, String bankAccount, String status) {
    }
}
