# -*- coding: utf-8 -*-
"""生成实名认证留痕服务 + 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['person/service/VerifyRecordService.java'] = '''package com.yundao.bp.person.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.person.entity.PersonVerifyRecord;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * 实名认证留痕服务。
 *
 * <p><b>为什么必须留痕</b>：实名认证是保障资格的入口，一旦出事（冒名申请）
 * 必须能追溯「谁在什么时候、通过什么渠道、用什么材料、结果如何」。
 * 因此本模块<b>只追加，不提供修改与删除</b>。
 *
 * <p>人脸比对结果按 IoT 规范有 6 种取值（1 同一人 / 2 不同人 / 3 不能确定 /
 * 4 无法比对 / 5 库中无照片 / 0 空），<b>不能只存「通过/不通过」</b>，
 * 否则无法区分「确认不是本人」与「照片糊了比对不了」。
 */
public interface VerifyRecordService {

    /** 记录一次认证（由认证调用方在拿到结果后写入）。 */
    PersonVerifyRecord record(Long personId, String verifyType, String userName,
                              String idCardHash, String faceImgUrl, String idcardImgUrl,
                              String commandId, String responseCode, String resultCode,
                              BigDecimal faceScore, String faceResult,
                              String citizenResult, String rawResponse);

    PersonVerifyRecord get(Long id);

    PageResult<PersonVerifyRecord> page(long pageNum, long pageSize, Long personId,
                                        String verifyType, Boolean passOnly);

    /** ⭐ 某人的认证结论（用于申请校验时快速判断）。 */
    Map<String, Object> conclusion(Long personId);

    /** 失败原因分布（运维/风控看板）。 */
    Map<String, Object> failStats();
}
'''

F['person/service/impl/VerifyRecordServiceImpl.java'] = '''package com.yundao.bp.person.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.person.entity.PersonVerifyRecord;
import com.yundao.bp.person.mapper.PersonVerifyRecordMapper;
import com.yundao.bp.person.service.VerifyRecordService;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 实名认证留痕实现。
 */
@Service
public class VerifyRecordServiceImpl implements VerifyRecordService {

    private static final Logger log = LoggerFactory.getLogger(VerifyRecordServiceImpl.class);
    private static final com.fasterxml.jackson.databind.ObjectMapper JSON =
            new com.fasterxml.jackson.databind.ObjectMapper();

    private final PersonVerifyRecordMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public VerifyRecordServiceImpl(PersonVerifyRecordMapper mapper,
                                   SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonVerifyRecord record(Long personId, String verifyType, String userName,
                                     String idCardHash, String faceImgUrl,
                                     String idcardImgUrl, String commandId,
                                     String responseCode, String resultCode,
                                     BigDecimal faceScore, String faceResult,
                                     String citizenResult, String rawResponse) {
        if (verifyType == null || verifyType.isBlank()) {
            throw BizException.paramInvalid("认证类型不能为空");
        }
        boolean pass = judge(faceResult, citizenResult);
        String failReason = pass ? null : explainFail(faceResult, citizenResult);

        PersonVerifyRecord r = new PersonVerifyRecord();
        r.setId(idGen.nextId());
        r.setTenantId(TenantContext.tenantId());
        r.setPersonId(personId);
        r.setVerifyType(verifyType);
        r.setUserName(userName);
        r.setIdCardHash(idCardHash);
        r.setFaceImgUrl(faceImgUrl);
        r.setIdcardImgUrl(idcardImgUrl);
        r.setRequestNo("VR" + r.getId());
        r.setCommandId(commandId);
        r.setResponseCode(responseCode);
        r.setResultCode(resultCode);
        r.setFaceScore(faceScore);
        r.setFaceResult(faceResult);
        r.setCitizenResult(citizenResult);
        r.setVerifyPass(pass ? 1 : 0);
        r.setFailReason(failReason);
        r.setRawResponse(truncate(rawResponse));
        r.setCreateTime(LocalDateTime.now());
        mapper.insert(r);
        log.info("实名认证留痕：人员 {} 类型 {} → {}", personId, verifyType,
                pass ? "通过" : "不通过（" + failReason + "）");
        return r;
    }

    /**
     * 判定是否通过。
     *
     * <p>规则：人脸结果为「1 同一人」<b>且</b>身份核查不是「2 不一致/3 库中无此号」。
     * 只比人脸不看身份核查会被冒用；只看身份核查不看人脸会被照片欺骗。
     */
    static boolean judge(String faceResult, String citizenResult) {
        boolean faceOk = "1".equals(faceResult);
        boolean citizenBad = "2".equals(citizenResult) || "3".equals(citizenResult);
        if (!faceOk) {
            return false;
        }
        return !citizenBad;
    }

    /** 失败原因（要能区分「确认不是本人」与「比对不了」）。 */
    static String explainFail(String faceResult, String citizenResult) {
        if ("2".equals(faceResult)) {
            return "人脸比对判定为不同人（疑似冒用身份）";
        }
        if ("3".equals(faceResult)) {
            return "人脸比对不能确定（建议重新采集或转人工核验）";
        }
        if ("4".equals(faceResult)) {
            return "无法比对（照片质量不合格，请重新上传）";
        }
        if ("5".equals(faceResult)) {
            return "公安库中无该照片，无法比对";
        }
        if ("2".equals(citizenResult)) {
            return "身份核查不一致（姓名与身份证号不匹配）";
        }
        if ("3".equals(citizenResult)) {
            return "身份证库中查无此号";
        }
        if (faceResult == null || "0".equals(faceResult)) {
            return "未取得人脸比对结果";
        }
        return "认证未通过";
    }

    @Override
    public PersonVerifyRecord get(Long id) {
        PersonVerifyRecord r = mapper.selectById(id);
        if (r == null) {
            throw BizException.notFound("认证记录");
        }
        return r;
    }

    @Override
    public PageResult<PersonVerifyRecord> page(long pageNum, long pageSize, Long personId,
                                               String verifyType, Boolean passOnly) {
        LambdaQueryWrapper<PersonVerifyRecord> qw =
                new LambdaQueryWrapper<PersonVerifyRecord>()
                        .eq(personId != null, PersonVerifyRecord::getPersonId, personId)
                        .eq(verifyType != null && !verifyType.isBlank(),
                                PersonVerifyRecord::getVerifyType, verifyType)
                        .eq(Boolean.TRUE.equals(passOnly),
                                PersonVerifyRecord::getVerifyPass, 1)
                        .orderByDesc(PersonVerifyRecord::getId);
        IPage<PersonVerifyRecord> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    public Map<String, Object> conclusion(Long personId) {
        List<PersonVerifyRecord> list = mapper.selectList(
                new LambdaQueryWrapper<PersonVerifyRecord>()
                        .eq(PersonVerifyRecord::getPersonId, personId)
                        .orderByDesc(PersonVerifyRecord::getId));
        Map<String, Object> m = new LinkedHashMap<>();
        if (list.isEmpty()) {
            m.put("personId", personId);
            m.put("verified", false);
            m.put("hasRecord", false);
            m.put("conclusion", "无认证记录，不可进入资格审核");
            return m;
        }
        PersonVerifyRecord latest = list.get(0);
        boolean passed = latest.getVerifyPass() != null && latest.getVerifyPass() == 1;
        m.put("personId", personId);
        m.put("hasRecord", true);
        m.put("verified", passed);
        m.put("totalAttempts", list.size());
        m.put("latestVerifyType", latest.getVerifyType());
        m.put("latestPass", passed);
        m.put("latestFailReason", latest.getFailReason());
        m.put("latestTime", latest.getCreateTime());
        m.put("conclusion", passed
                ? "实名认证已通过（" + latest.getVerifyType() + "）"
                : "最近一次认证未通过：" + latest.getFailReason() + "，需重新认证");
        return m;
    }

    @Override
    public Map<String, Object> failStats() {
        List<PersonVerifyRecord> fails = mapper.selectList(
                new LambdaQueryWrapper<PersonVerifyRecord>()
                        .eq(PersonVerifyRecord::getVerifyPass, 0));
        Map<String, Integer> byReason = new LinkedHashMap<>();
        Map<String, Integer> byType = new LinkedHashMap<>();
        for (PersonVerifyRecord r : fails) {
            String reason = r.getFailReason() == null ? "未知" : r.getFailReason();
            byReason.merge(reason, 1, Integer::sum);
            byType.merge(r.getVerifyType() == null ? "-" : r.getVerifyType(), 1,
                    Integer::sum);
        }
        Long total = mapper.selectCount(new LambdaQueryWrapper<>());
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("total", total == null ? 0 : total);
        m.put("failed", fails.size());
        m.put("failRate", total == null || total == 0 ? 0.0
                : Math.round(fails.size() * 10000.0 / total) / 100.0);
        m.put("byReason", byReason);
        m.put("byType", byType);
        return m;
    }

    private static String truncate(String s) {
        if (s == null) {
            return null;
        }
        if (s.length() <= 4000) {
            return s;
        }
        return s.substring(0, 4000) + "...(截断)";
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
