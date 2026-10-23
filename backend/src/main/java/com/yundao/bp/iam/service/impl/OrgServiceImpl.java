package com.yundao.bp.iam.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.dto.OrgCreateCmd;
import com.yundao.bp.iam.dto.OrgVO;
import com.yundao.bp.iam.entity.IamOrg;
import com.yundao.bp.iam.mapper.IamOrgMapper;
import com.yundao.bp.iam.service.OrgService;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 组织服务实现。
 *
 * <p>多租户要点：<b>不手写 tenant_id 条件</b>，由 MyBatis-Plus 租户插件自动追加；
 * 但插入时必须显式设置 {@code tenantId}（插件只管查询/更新，不管 insert 赋值）。
 */
@Service
public class OrgServiceImpl implements OrgService {

    private final IamOrgMapper orgMapper;
    private final SnowflakeIdGenerator idGen;

    public OrgServiceImpl(IamOrgMapper orgMapper, SnowflakeIdGenerator idGen) {
        this.orgMapper = orgMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrgVO create(OrgCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // 编码租户内唯一（插件已自动限定租户，故此处不带 tenant_id）
        Long dup = orgMapper.selectCount(new LambdaQueryWrapper<IamOrg>()
                .eq(IamOrg::getOrgCode, cmd.orgCode()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "组织编码已存在: " + cmd.orgCode());
        }

        // 计算 path / level（父为空则顶级）
        String orgPath = "";
        int level = 1;
        if (cmd.parentId() != null) {
            IamOrg parent = orgMapper.selectById(cmd.parentId());
            if (parent == null) {
                throw BizException.notFound("父组织");
            }
            level = (parent.getOrgLevel() == null ? 1 : parent.getOrgLevel()) + 1;
            orgPath = (parent.getOrgPath() == null ? "" : parent.getOrgPath())
                    + parent.getId() + "/";
        }

        IamOrg e = new IamOrg();
        e.setId(idGen.nextId());
        e.setTenantId(tenantId);
        e.setOrgCode(cmd.orgCode());
        e.setOrgName(cmd.orgName());
        e.setParentId(cmd.parentId());
        e.setOrgPath(orgPath);
        e.setOrgLevel(level);
        e.setOrgType(cmd.orgType());
        e.setProvince(cmd.province());
        e.setCity(cmd.city());
        e.setDistrict(cmd.district());
        e.setStreet(cmd.street());
        e.setCommunity(cmd.community());
        e.setAddress(cmd.address());
        e.setSortNo(cmd.sortNo() == null ? 0 : cmd.sortNo());
        e.setStatus("ENABLED");
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);

        orgMapper.insert(e);
        return OrgVO.from(e);
    }

    @Override
    public OrgVO get(Long id) {
        IamOrg e = orgMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("组织");
        }
        return OrgVO.from(e);
    }

    @Override
    public PageResult<OrgVO> page(long pageNum, long pageSize, String keyword,
                                  Long parentId, Boolean includeSubtree) {
        LambdaQueryWrapper<IamOrg> qw = new LambdaQueryWrapper<IamOrg>()
                .orderByAsc(IamOrg::getSortNo)
                .orderByAsc(IamOrg::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(IamOrg::getOrgName, keyword)
                    .or().like(IamOrg::getOrgCode, keyword));
        }
        if (parentId != null) {
            if (Boolean.TRUE.equals(includeSubtree)) {
                // 含下级：org_path 存的是「祖先路径」且不含自身，
                // 因此血缘前缀必须是 path + 自身id + "/"，否则根节点 path 为空
                // 会匹配到全表。
                IamOrg parent = orgMapper.selectById(parentId);
                if (parent == null) {
                    return PageResult.empty(pageNum, pageSize);
                }
                String base = parent.getOrgPath() == null ? "" : parent.getOrgPath();
                String lineage = base + parentId + "/";
                qw.and(w -> w.likeRight(IamOrg::getOrgPath, lineage)
                        .or().eq(IamOrg::getId, parentId));
            } else {
                // 默认只取直接下级，符合「点节点看其子组织」的直觉
                qw.eq(IamOrg::getParentId, parentId);
            }
        }
        IPage<IamOrg> page = orgMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<OrgVO> rows = page.getRecords().stream().map(OrgVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<OrgVO> children(Long parentId) {
        LambdaQueryWrapper<IamOrg> qw = new LambdaQueryWrapper<IamOrg>()
                .eq(parentId != null, IamOrg::getParentId, parentId)
                .orderByAsc(IamOrg::getSortNo);
        return orgMapper.selectList(qw).stream().map(OrgVO::from).toList();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(Long id) {
        Long kids = orgMapper.selectCount(new LambdaQueryWrapper<IamOrg>()
                .eq(IamOrg::getParentId, id));
        if (kids != null && kids > 0) {
            throw BizException.stateConflict("存在下级组织，不允许删除");
        }
        if (orgMapper.deleteById(id) == 0) {
            throw BizException.notFound("组织");
        }
    }
}
