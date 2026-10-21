package com.yundao.bp.person.service.impl;

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
    /** 列表要带出人员姓名与脱敏信息，避免只显示一串 ID */
    private final com.yundao.bp.person.mapper.PersonMapper personMapper;

    public VerifyRecordServiceImpl(PersonVerifyRecordMapper mapper,
                                   SnowflakeIdGenerator idGen,
                                   com.yundao.bp.person.mapper.PersonMapper personMapper) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.personMapper = personMapper;
    }

    /** 给核验流水补齐人员姓名与脱敏手机/证件号 */
    private void fillPersonInfo(List<PersonVerifyRecord> list) {
        if (list == null || list.isEmpty()) {
            return;
        }
        java.util.List<Long> ids = new java.util.ArrayList<>();
        for (PersonVerifyRecord r : list) {
            if (r.getPersonId() != null) {
                ids.add(r.getPersonId());
            }
        }
        if (ids.isEmpty()) {
            return;
        }
        java.util.Map<Long, com.yundao.bp.person.entity.Person> byId = new java.util.HashMap<>();
        for (com.yundao.bp.person.entity.Person p : personMapper.selectBatchIds(ids)) {
            byId.put(p.getId(), p);
        }
        for (PersonVerifyRecord r : list) {
            com.yundao.bp.person.entity.Person p = byId.get(r.getPersonId());
            if (p == null) {
                continue;
            }
            r.setPersonName(p.getPersonName());
            r.setPhoneMask(mask(p.getPhone(), 3, 4));
            r.setIdCardMask(mask(p.getIdCard(), 6, 4));
        }
    }

    private static String mask(String raw, int head, int tail) {
        if (raw == null || raw.isBlank()) {
            return "";
        }
        int len = raw.length();
        if (len <= head + tail) {
            return raw.charAt(0) + "****";
        }
        return raw.substring(0, head) + "****" + raw.substring(len - tail);
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
        fillPersonInfo(page.getRecords());
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
