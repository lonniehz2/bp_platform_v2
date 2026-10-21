# -*- coding: utf-8 -*-
"""生成保障对象档案 + 实名认证留痕：实体 + Mapper + 常量 + 服务"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def ent(name, table, fields, doc, logic=False):
    li = 'import com.baomidou.mybatisplus.annotation.TableLogic;\n' if logic else ''
    lg = '\n    @TableLogic\n    private Integer isDeleted;\n' if logic else ''
    return f'''package com.yundao.bp.person.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
{li}import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{chr(10).join(fields)}
{lg}}}
'''


F['person/entity/PersonGuaranteeProfile.java'] = ent(
    'PersonGuaranteeProfile', 'bp_person_guarantee_profile', [
        '    private String tenantId;',
        '    private Long personId;',
        '    /** PUBLIC / AFFORDABLE / TALENT / LOW_RENT */',
        '    private String securityType;',
        '    /** 家庭人口数（决定保障面积/补贴） */',
        '    private Integer familySize;',
        '    /** SINGLE / COUPLE / WITH_CHILD / WITH_ELDER / OTHER */',
        '    private String familyType;',
        '    private BigDecimal monthlyIncome;',
        '    /** LOW / LOW_INCOME / MIDDLE_LOW / NORMAL */',
        '    private String incomeLevel;',
        '    private BigDecimal assetDeclare;',
        '    private Integer hasHouse;',
        '    private Integer houseCount;',
        '    private Integer hasVehicle;',
        '    private String socialSecurity;',
        '    /** 优先条件（逗号分隔） */',
        '    private String priorityFlags;',
        '    private BigDecimal priorityScore;',
        '    private String talentLevel;',
        '    private String talentCertNo;',
        '    private LocalDate talentValidTo;',
        '    /** APPLICANT / UNDER_REVIEW / QUALIFIED / IN_RESIDENCE / EXITED */',
        '    private String profileStatus;',
        '    private LocalDate qualifyDate;',
        '    /** 资格有效期至（年审依据） */',
        '    private LocalDate qualifyExpire;',
        '    private LocalDate firstApplyDate;',
        '    private LocalDate lastReviewDate;',
        '    private LocalDate exitDate;',
        '    private String exitReason;',
        '    private String remark;',
        '    private String createBy;',
        '    private LocalDateTime createTime;',
        '    private String updateBy;',
        '    private LocalDateTime updateTime;',
    ], '保障对象专有档案。对应 `bp_person_guarantee_profile`。', True)

F['person/entity/PersonVerifyRecord.java'] = ent(
    'PersonVerifyRecord', 'bp_person_verify_record', [
        '    private String tenantId;',
        '    private Long personId;',
        '    /** PERSONAL / ORG / FACE_COMPARE / IDCARD_DECODE */',
        '    private String verifyType;',
        '    /** 提交的姓名（加密存储） */',
        '    private String userName;',
        '    /** 身份证哈希（可判等，不可反推） */',
        '    private String idCardHash;',
        '    private String faceImgUrl;',
        '    private String idcardImgUrl;',
        '    private String requestNo;',
        '    private String commandId;',
        '    private String responseCode;',
        '    private String resultCode;',
        '    private BigDecimal faceScore;',
        '    /** 0 null / 1 同一人 / 2 不同人 / 3 不能确定 / 4 无法比对 / 5 库中无照片 */',
        '    private String faceResult;',
        '    /** 1 一致 / 2 不一致 / 3 库中无此号 */',
        '    private String citizenResult;',
        '    private Integer verifyPass;',
        '    private String failReason;',
        '    private String rawResponse;',
        '    private LocalDateTime createTime;',
    ], '实名认证流水。对应 `bp_person_verify_record`。')

for n in ('PersonGuaranteeProfile', 'PersonVerifyRecord'):
    F['person/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.person.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.person.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== 收入档位推导（纯逻辑） ====================
F['person/constant/IncomeLevel.java'] = '''package com.yundao.bp.person.constant;

import java.math.BigDecimal;

/**
 * 收入档位。
 *
 * <p><b>为什么做成枚举+阈值可配</b>：各地低保线/中低收入线不同，
 * 且会逐年调整。阈值由调用方传入（来自系统参数），本枚举只负责<b>判定规则</b>，
 * 保证「同一套判定逻辑，不同地区不同阈值」。
 */
public enum IncomeLevel {

    LOW("低保"),
    LOW_INCOME("低收入"),
    MIDDLE_LOW("中低收入"),
    NORMAL("普通");

    private final String label;

    IncomeLevel(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /**
     * 按人均月收入判定档位。
     *
     * @param monthlyIncome   家庭月收入（元）
     * @param familySize      家庭人口
     * @param lowLine         低保线（人均月收入）
     * @param lowIncomeLine   低收入线
     * @param middleLowLine   中低收入线
     */
    public static IncomeLevel of(BigDecimal monthlyIncome, Integer familySize,
                                 BigDecimal lowLine, BigDecimal lowIncomeLine,
                                 BigDecimal middleLowLine) {
        if (monthlyIncome == null) {
            return NORMAL;
        }
        int size = (familySize == null || familySize <= 0) ? 1 : familySize;
        BigDecimal perCapita = monthlyIncome.divide(BigDecimal.valueOf(size), 2,
                java.math.RoundingMode.HALF_UP);
        if (lowLine != null && perCapita.compareTo(lowLine) <= 0) {
            return LOW;
        }
        if (lowIncomeLine != null && perCapita.compareTo(lowIncomeLine) <= 0) {
            return LOW_INCOME;
        }
        if (middleLowLine != null && perCapita.compareTo(middleLowLine) <= 0) {
            return MIDDLE_LOW;
        }
        return NORMAL;
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
