# -*- coding: utf-8 -*-
"""生成同住人模块 + 接入补贴按人计费"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/entity/BizContractCohabitant.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 合同同住人。对应 {@code bp_biz_contract_cohabitant}。
 *
 * <p>同住人是保障房的关键数据：<b>按人补贴</b>、<b>年审人口核查</b>、
 * <b>退租腾退</b>、<b>门禁授权</b>都依赖它。
 */
@Data
@TableName("bp_biz_contract_cohabitant")
public class BizContractCohabitant {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long contractId;
    private Long personId;

    private String memberName;
    /** 身份证脱敏（不存明文） */
    private String idCardMask;
    /** 与承租人关系 */
    private String relation;
    /** 是否已授权开门 */
    private Integer isGranted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
'''

FILES['biz/mapper/BizContractCohabitantMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizContractCohabitantMapper extends BaseMapper<BizContractCohabitant> {
}
'''

FILES['biz/dto/CohabitantCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * 添加合同同住人。
 *
 * <p>身份证只存<b>脱敏串</b>（如 110101********1234），不存明文。
 */
public record CohabitantCreateCmd(

        Long personId,

        @NotBlank(message = "同住人姓名不能为空")
        @Size(max = 64, message = "姓名不能超过 64 字符")
        String memberName,

        /** 身份证脱敏串（前端脱敏后传，或不传） */
        String idCardMask,

        /** 与承租人关系：SPOUSE 配偶 / CHILD 子女 / PARENT 父母 / SIBLING 兄弟姐妹 / OTHER 其他 */
        String relation,

        Integer isGranted
) {
}
'''

FILES['biz/dto/CohabitantVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.entity.BizContractCohabitant;
import java.time.LocalDateTime;

/**
 * 同住人视图。
 */
public record CohabitantVO(
        Long id,
        Long contractId,
        Long personId,
        String memberName,
        String idCardMask,
        String relation,
        String relationLabel,
        Boolean granted,
        LocalDateTime createTime
) {
    public static CohabitantVO from(BizContractCohabitant e) {
        if (e == null) {
            return null;
        }
        return new CohabitantVO(e.getId(), e.getContractId(), e.getPersonId(),
                e.getMemberName(), e.getIdCardMask(), e.getRelation(),
                relationLabel(e.getRelation()),
                e.getIsGranted() != null && e.getIsGranted() == 1, e.getCreateTime());
    }

    /** 关系中文标签。 */
    public static String relationLabel(String relation) {
        if (relation == null) {
            return "其他";
        }
        return switch (relation) {
            case "SPOUSE" -> "配偶";
            case "CHILD" -> "子女";
            case "PARENT" -> "父母";
            case "SIBLING" -> "兄弟姐妹";
            default -> "其他";
        };
    }
}
'''

FILES['biz/service/CohabitantService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.CohabitantCreateCmd;
import com.yundao.bp.biz.dto.CohabitantVO;
import java.util.List;

/**
 * 合同同住人服务。
 *
 * <p>⭐ <b>保障人口口径（决策 D24）</b>：
 * {@code 保障人口 = 承租人 1 人 + 同住人数}。
 * 按人补贴、年审人均收入核查、退租腾退家庭人数均按此口径计算。
 */
public interface CohabitantService {

    /** 添加同住人（同一合同内姓名不可重复）。 */
    CohabitantVO add(Long contractId, CohabitantCreateCmd cmd);

    /** 列同住人。 */
    List<CohabitantVO> list(Long contractId);

    CohabitantVO get(Long id);

    /** 移除同住人。 */
    void remove(Long id);

    /** 设置门禁开门授权。 */
    CohabitantVO setGranted(Long id, boolean granted);

    /**
     * 保障人口数 = 承租人 1 + 同住人数。
     *
     * <p>供按人补贴、年审核查调用。
     */
    int householdSize(Long contractId);
}
'''

FILES['biz/service/impl/CohabitantServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.dto.CohabitantCreateCmd;
import com.yundao.bp.biz.dto.CohabitantVO;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.service.CohabitantService;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 合同同住人实现。
 */
@Service
public class CohabitantServiceImpl implements CohabitantService {

    private static final Logger log = LoggerFactory.getLogger(CohabitantServiceImpl.class);

    private final BizContractCohabitantMapper mapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;

    public CohabitantServiceImpl(BizContractCohabitantMapper mapper,
                                 BizContractMapper contractMapper,
                                 SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CohabitantVO add(Long contractId, CohabitantCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        BizContract ct = contractMapper.selectById(contractId);
        if (ct == null) {
            throw BizException.notFound("合同");
        }
        ContractStatus st;
        try {
            st = ContractStatus.valueOf(ct.getContractStatus());
        } catch (IllegalArgumentException e) {
            st = ContractStatus.DRAFT;
        }
        if (st.isTerminal()) {
            throw BizException.stateConflict("合同已" + st.label() + "，不可添加同住人");
        }
        // 同一合同内姓名不可重复
        Long dup = mapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
                .eq(BizContractCohabitant::getContractId, contractId)
                .eq(BizContractCohabitant::getMemberName, cmd.memberName().trim()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("该合同已有同名同住人：" + cmd.memberName().trim());
        }

        long id = idGen.nextId();
        BizContractCohabitant e = new BizContractCohabitant();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setContractId(contractId);
        e.setPersonId(cmd.personId());
        e.setMemberName(cmd.memberName().trim());
        e.setIdCardMask(cmd.idCardMask());
        e.setRelation(normalizeRelation(cmd.relation()));
        e.setIsGranted(cmd.isGranted() == null ? 0 : cmd.isGranted());
        e.setCreateTime(LocalDateTime.now());
        mapper.insert(e);
        log.info("合同 {} 添加同住人 {}（{}）", ct.getContractNo(), e.getMemberName(),
                CohabitantVO.relationLabel(e.getRelation()));
        return CohabitantVO.from(e);
    }

    @Override
    public List<CohabitantVO> list(Long contractId) {
        return mapper.selectList(new LambdaQueryWrapper<BizContractCohabitant>()
                        .eq(BizContractCohabitant::getContractId, contractId)
                        .orderByAsc(BizContractCohabitant::getId))
                .stream().map(CohabitantVO::from).toList();
    }

    @Override
    public CohabitantVO get(Long id) {
        BizContractCohabitant e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("同住人");
        }
        return CohabitantVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void remove(Long id) {
        BizContractCohabitant e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("同住人");
        }
        mapper.deleteById(id);
        log.info("合同 {} 移除同住人 {}", e.getContractId(), e.getMemberName());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CohabitantVO setGranted(Long id, boolean granted) {
        BizContractCohabitant e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("同住人");
        }
        e.setIsGranted(granted ? 1 : 0);
        mapper.updateById(e);
        return CohabitantVO.from(e);
    }

    @Override
    public int householdSize(Long contractId) {
        Long n = mapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
                .eq(BizContractCohabitant::getContractId, contractId));
        return 1 + (n == null ? 0 : n.intValue());
    }

    private static String normalizeRelation(String relation) {
        if (relation == null || relation.isBlank()) {
            return "OTHER";
        }
        return switch (relation) {
            case "SPOUSE", "CHILD", "PARENT", "SIBLING" -> relation;
            default -> "OTHER";
        };
    }
}
'''

FILES['biz/controller/CohabitantController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.CohabitantCreateCmd;
import com.yundao.bp.biz.dto.CohabitantVO;
import com.yundao.bp.biz.service.CohabitantService;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 合同同住人接口（BC-05）。
 *
 * <p>同住人用于：按人补贴、年审人口核查、退租腾退、门禁授权。
 */
@RestController
@RequestMapping("/api/v1/contracts/{contractId}/cohabitants")
public class CohabitantController {

    private final CohabitantService service;

    public CohabitantController(CohabitantService service) {
        this.service = service;
    }

    @PostMapping
    public R<CohabitantVO> add(@PathVariable Long contractId,
                               @Valid @RequestBody CohabitantCreateCmd cmd) {
        return R.ok(service.add(contractId, cmd));
    }

    @GetMapping
    public R<List<CohabitantVO>> list(@PathVariable Long contractId) {
        return R.ok(service.list(contractId));
    }

    /** 保障人口数（承租人 1 + 同住人）。 */
    @GetMapping("/household-size")
    public R<Integer> householdSize(@PathVariable Long contractId) {
        return R.ok(service.householdSize(contractId));
    }

    @GetMapping("/{id}")
    public R<CohabitantVO> get(@PathVariable Long contractId, @PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @DeleteMapping("/{id}")
    public R<Void> remove(@PathVariable Long contractId, @PathVariable Long id) {
        service.remove(id);
        return R.ok(null);
    }

    /** 门禁开门授权。 */
    @PostMapping("/{id}/grant")
    public R<CohabitantVO> grant(@PathVariable Long contractId, @PathVariable Long id,
                                 @RequestBody GrantCmd cmd) {
        return R.ok(service.setGranted(id, cmd.granted()));
    }

    public record GrantCmd(boolean granted) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
