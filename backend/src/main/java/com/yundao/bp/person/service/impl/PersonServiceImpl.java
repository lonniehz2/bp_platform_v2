package com.yundao.bp.person.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.person.dto.PersonCreateCmd;
import com.yundao.bp.person.dto.PersonVO;
import com.yundao.bp.person.entity.Person;
import com.yundao.bp.person.mapper.PersonMapper;
import com.yundao.bp.person.service.PersonService;
import com.yundao.bp.person.util.SensitiveDataCodec;
import java.util.List;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 人员服务实现。
 *
 * <p>敏感数据写入纪律：
 * <ol>
 *   <li>明文校验（身份证校验位）</li>
 *   <li>写 {@code *_hash}（用于唯一性校验与精确检索）</li>
 *   <li>写 {@code *_mask}（用于展示）</li>
 *   <li>写原文到 {@code xxx}（<b>当前放在明文字段中占位</b>，
 *       生产须接入 KMS 加密后再存，见下方 TODO）</li>
 * </ol>
 */
@Service
public class PersonServiceImpl implements PersonService {

    private static final Set<String> VALID_STATUS = Set.of("NORMAL", "BLACKLIST", "CANCELLED");

    private final PersonMapper personMapper;
    private final com.yundao.bp.iam.mapper.IamOrgMapper orgMapper;

    /** 取某组织及其所有下级组织的 ID（按 org_path 前缀匹配） */
    private java.util.List<Long> orgSubtreeIds(Long orgId) {
        // 逐层按 parent_id 展开，不依赖 org_path ——
        // 根节点的 org_path 是空串，用 startsWith 会匹配到全部组织（曾导致「含下级」返回全量）
        java.util.List<com.yundao.bp.iam.entity.IamOrg> all = orgMapper.selectList(null);
        java.util.Set<Long> ids = new java.util.LinkedHashSet<>();
        ids.add(orgId);
        java.util.Set<Long> frontier = new java.util.HashSet<>();
        frontier.add(orgId);
        for (int round = 0; round < 10 && !frontier.isEmpty(); round++) {
            java.util.Set<Long> next = new java.util.HashSet<>();
            for (com.yundao.bp.iam.entity.IamOrg o : all) {
                if (o.getParentId() != null && frontier.contains(o.getParentId())
                        && ids.add(o.getId())) {
                    next.add(o.getId());
                }
            }
            frontier = next;
        }
        return new java.util.ArrayList<>(ids);
    }

    private final SnowflakeIdGenerator idGen;

    public PersonServiceImpl(PersonMapper personMapper,
                             com.yundao.bp.iam.mapper.IamOrgMapper orgMapper, SnowflakeIdGenerator idGen) {
        this.personMapper = personMapper;
        this.orgMapper = orgMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonVO create(PersonCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        String idCard = trim(cmd.idCard());
        String phone = trim(cmd.phone());

        // 1) 格式与校验位
        if (idCard != null) {
            if (!SensitiveDataCodec.isValidIdCard(idCard)) {
                throw BizException.paramInvalid("身份证号格式不正确");
            }
            if (idCard.length() == 18 && !SensitiveDataCodec.verifyIdCardChecksum(idCard)) {
                throw BizException.paramInvalid("身份证号校验位不正确");
            }
        }
        if (phone != null && !SensitiveDataCodec.isValidPhone(phone)) {
            throw BizException.paramInvalid("手机号格式不正确");
        }

        // 2) 身份证唯一性（走哈希列，精确匹配）
        if (idCard != null) {
            String hash = SensitiveDataCodec.hash(idCard);
            Long dup = personMapper.selectCount(new LambdaQueryWrapper<Person>()
                    .eq(Person::getIdCardHash, hash));
            if (dup != null && dup > 0) {
                throw new BizException(ErrorCode.DUPLICATED, "该身份证号已存在人员档案");
            }
        }

        long id = idGen.nextId();
        Person p = new Person();
        p.setId(id);
        p.setTenantId(tenantId);
        p.setPersonCode("P" + id);
        p.setPersonName(cmd.personName());
        p.setRealName(cmd.personName());

        // 3) 敏感字段三列
        if (phone != null) {
            // TODO 生产：phone 应存 AES 密文（接入 KMS）
            p.setPhone(phone);
            p.setPhoneHash(SensitiveDataCodec.hash(phone));
        }
        if (idCard != null) {
            // TODO 生产：idCard 应存 AES 密文（接入 KMS）
            p.setIdCard(idCard);
            p.setIdCardHash(SensitiveDataCodec.hash(idCard));
            p.setIdCardMask(SensitiveDataCodec.maskIdCard(idCard));
            // 4) 从身份证派生性别与生日（缺失时填充）
            p.setBirthday(SensitiveDataCodec.birthdayFromIdCard(idCard));
            if (p.getBirthday() != null) {
                p.setGender(SensitiveDataCodec.genderFromIdCard(idCard));
            }
        }

        p.setOrgId(cmd.orgId());
        p.setHouseholdType(blankToNull(cmd.householdType()));
        p.setMaritalStatus(blankToNull(cmd.maritalStatus()));
        p.setEducation(cmd.education());
        p.setEmployer(cmd.employer());
        p.setRemark(cmd.remark());
        p.setPersonSource("ADMIN");
        p.setVerifyStatus("UNVERIFIED");
        p.setVerifyLevel("NONE");
        p.setPersonStatus("NORMAL");
        p.setPrivacyFlag(0);
        p.setIsDeleted(0);

        personMapper.insert(p);
        return PersonVO.from(p);
    }

    @Override
    public PersonVO get(Long id) {
        Person p = personMapper.selectById(id);
        if (p == null) {
            throw BizException.notFound("人员");
        }
        return PersonVO.from(p);
    }

    @Override
    public PageResult<PersonVO> page(long pageNum, long pageSize, String keyword,
                                     Long orgId, String personStatus,
                                     Boolean includeChildren) {
        LambdaQueryWrapper<Person> qw = new LambdaQueryWrapper<Person>()
                .eq(orgId != null && !Boolean.TRUE.equals(includeChildren),
                        Person::getOrgId, orgId)
                .eq(personStatus != null && !personStatus.isBlank(),
                        Person::getPersonStatus, personStatus)
                .orderByDesc(Person::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(Person::getPersonName, keyword)
                    .or().like(Person::getPersonCode, keyword)
                    .or().like(Person::getPhone, keyword)
                    .or().like(Person::getIdCard, keyword));
        }
        // 含下级：按 org_path 前缀取整棵子树（组织是树，见 bp_iam_org 的 parent_id/org_path）
        if (orgId != null && Boolean.TRUE.equals(includeChildren)) {
            java.util.List<Long> ids = orgSubtreeIds(orgId);
            if (ids.isEmpty()) {
                return PageResult.of(0, pageNum, pageSize, new java.util.ArrayList<>());
            }
            qw.in(Person::getOrgId, ids);
        }
        IPage<Person> page = personMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<PersonVO> rows = page.getRecords().stream().map(PersonVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public PersonVO findByIdCard(String idCard) {
        if (idCard == null || idCard.isBlank()) {
            throw BizException.paramInvalid("身份证号不能为空");
        }
        Person p = personMapper.selectOne(new LambdaQueryWrapper<Person>()
                .eq(Person::getIdCardHash, SensitiveDataCodec.hash(idCard.trim()))
                .last("LIMIT 1"));
        return p == null ? null : PersonVO.from(p);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonVO update(Long id, com.yundao.bp.person.dto.PersonUpdateCmd cmd) {
        if (id == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("人员ID不能为空");
        }
        Person e = personMapper.selectById(id);
        if (e == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("人员");
        }
        // 只覆盖非空字段：前端未传的不清空，避免误删已有信息
        if (cmd.personName() != null && !cmd.personName().isBlank()) {
            e.setPersonName(cmd.personName());
        }
        if (cmd.phone() != null && !cmd.phone().isBlank()) {
            e.setPhone(cmd.phone());
        }
        if (cmd.orgId() != null) {
            e.setOrgId(cmd.orgId());
        }
        if (cmd.householdType() != null && !cmd.householdType().isBlank()) {
            e.setHouseholdType(cmd.householdType());
        }
        if (cmd.maritalStatus() != null && !cmd.maritalStatus().isBlank()) {
            e.setMaritalStatus(cmd.maritalStatus());
        }
        if (cmd.education() != null && !cmd.education().isBlank()) {
            e.setEducation(cmd.education());
        }
        if (cmd.employer() != null && !cmd.employer().isBlank()) {
            e.setEmployer(cmd.employer());
        }
        if (cmd.remark() != null) {
            e.setRemark(cmd.remark());
        }
        personMapper.updateById(e);
        return PersonVO.from(e);
    }

    public PersonVO changeStatus(Long id, String targetStatus) {
        if (!VALID_STATUS.contains(targetStatus)) {
            throw BizException.paramInvalid("状态值不合法: " + targetStatus
                    + "（只能是 NORMAL / BLACKLIST / CANCELLED）");
        }
        Person p = personMapper.selectById(id);
        if (p == null) {
            throw BizException.notFound("人员");
        }
        if (targetStatus.equals(p.getPersonStatus())) {
            return PersonVO.from(p);
        }
        if ("CANCELLED".equals(p.getPersonStatus())) {
            throw BizException.stateConflict("已注销人员不允许变更状态");
        }
        p.setPersonStatus(targetStatus);
        personMapper.updateById(p);
        return PersonVO.from(p);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(Long id) {
        Person p = personMapper.selectById(id);
        if (p == null) {
            throw BizException.notFound("人员");
        }
        if ("BLACKLIST".equals(p.getPersonStatus())) {
            throw BizException.stateConflict("黑名单人员不允许删除，请先解除黑名单");
        }
        if (personMapper.deleteById(id) == 0) {
            throw BizException.notFound("人员");
        }
    }

    private static String trim(String s) {
        return (s == null || s.isBlank()) ? null : s.trim();
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
