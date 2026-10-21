# -*- coding: utf-8 -*-
"""复议决定回写原业务：恢复资格真正撤销不利决定"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'biz\service\impl\AppealServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'applyEffect' in s:
    print('已接入，跳过')
    raise SystemExit

# ---------- 1) imports ----------
s = s.replace('import com.yundao.bp.biz.mapper.BizAppealMapper;',
              'import com.yundao.bp.biz.dto.ChangeCreateCmd;\n'
              'import com.yundao.bp.biz.dto.ChangeVO;\n'
              'import com.yundao.bp.biz.dto.TerminationVO;\n'
              'import com.yundao.bp.biz.entity.BizAnnualReview;\n'
              'import com.yundao.bp.biz.entity.BizContractChange;\n'
              'import com.yundao.bp.biz.mapper.BizAnnualReviewMapper;\n'
              'import com.yundao.bp.biz.mapper.BizAppealMapper;\n'
              'import com.yundao.bp.biz.mapper.BizContractChangeMapper;\n'
              'import com.yundao.bp.biz.service.ContractChangeService;\n'
              'import com.yundao.bp.biz.service.TerminationService;', 1)

s = s.replace('import java.time.LocalDateTime;',
              'import com.fasterxml.jackson.databind.ObjectMapper;\n'
              'import java.math.BigDecimal;\n'
              'import java.time.LocalDate;\n'
              'import java.time.LocalDateTime;\n'
              'import java.util.LinkedHashMap;', 1)

# ---------- 2) 依赖 ----------
s = s.replace('''    private final BizAppealMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public AppealServiceImpl(BizAppealMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }''',
              '''    private static final ObjectMapper JSON = new ObjectMapper();

    private final BizAppealMapper mapper;
    private final SnowflakeIdGenerator idGen;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private BizAnnualReviewMapper reviewMapper;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private BizContractChangeMapper changeMapper;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ContractChangeService contractChangeService;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private TerminationService terminationService;

    public AppealServiceImpl(BizAppealMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }''', 1)

# ---------- 3) decide() 后调用回写 ----------
old_end = '''        log.info("申诉 {} 决定：{}，影响 {}（{}）", e.getAppealNo(),
                target.label(), re.label(),
                cmd.reviewOpinion() == null ? "" : cmd.reviewOpinion());
        return AppealVO.from(e);'''
new_end = '''        // ⭐ 决定后回写原业务（决策 D29）：
        // 仅记录复议结论而不改变原决定，等于住户白申诉
        String effectNote = applyEffect(e, re, cmd);

        log.info("申诉 {} 决定：{}，影响 {}{}", e.getAppealNo(),
                target.label(), re.label(),
                effectNote == null ? "" : "；" + effectNote);
        return AppealVO.from(e);'''
assert old_end in s, 'decide 出口锚点缺失'
s = s.replace(old_end, new_end, 1)

# ---------- 4) 回写实现 ----------
anchor = '''    // ==================== 内部 ===================='''
helper = '''    /**
     * 把复议结果<b>真正落到原业务</b>上。
     *
     * <p>处理的场景：
     * <ol>
     *   <li>{@code ANNUAL_REVIEW} + {@code RESTORE}：年审结论改回「保留资格」，
     *       并把此前的调租变更<b>反向恢复</b>（按原租金再发起一笔变更，保留审计链）</li>
     *   <li>{@code EXIT} + {@code RESTORE}：撤销年审自动生成的退租腾退单</li>
     *   <li>其它组合：仅记录，需人工处置</li>
     * </ol>
     *
     * @return 处置说明（写入日志与复核意见）
     */
    private String applyEffect(BizAppeal e, AppealResultEffect re, AppealDecisionCmd cmd) {
        if (!re.changesOutcome()) {
            return null;
        }
        StringBuilder note = new StringBuilder();

        // ① 年度核查类：恢复资格 = 撤销调租 + 年审结论改 KEEP
        if ("ANNUAL_REVIEW".equals(e.getBizType()) && re == AppealResultEffect.RESTORE) {
            if (reviewMapper == null) {
                note.append("年审组件不可用，需人工恢复");
            } else {
                BizAnnualReview rv = reviewMapper.selectById(e.getBizId());
                if (rv == null) {
                    note.append("年审单不存在，需人工核实");
                } else {
                    // 反向恢复租金
                    String revert = revertRentChange(rv.getContractId());
                    if (revert != null) {
                        note.append(revert);
                    }
                    // 年审结论改回保留
                    rv.setReviewResult("KEEP");
                    rv.setAdjustContent((rv.getAdjustContent() == null ? ""
                            : rv.getAdjustContent())
                            + "｜经复议（" + e.getAppealNo() + "）异议成立，恢复原保障资格");
                    rv.setUpdateTime(LocalDateTime.now());
                    reviewMapper.updateById(rv);
                    if (note.length() > 0) {
                        note.append("；");
                    }
                    note.append("年审结论已恢复为「保留资格」");
                }
            }
        }

        // ② 退出类：撤销自动生成的退租腾退单
        if ("EXIT".equals(e.getBizType()) && re == AppealResultEffect.RESTORE) {
            String cancel = cancelAutoTermination(e);
            if (cancel != null) {
                if (note.length() > 0) {
                    note.append("；");
                }
                note.append(cancel);
            }
        }

        // ③ 其它组合：明确告知需人工
        if (note.length() == 0) {
            note.append("复议结论已记录；该业务类型（").append(e.getBizType())
                    .append("）的结果影响需人工处置");
        }

        // 把处置结果追加到复核意见，便于审计
        String op = cmd.reviewOpinion() == null ? "" : cmd.reviewOpinion();
        e.setReviewOpinion(op + "｜处置：" + note);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return note.toString();
    }

    /**
     * 反向恢复租金：找到该合同最近一笔已批准的「租金调整」，
     * 取其变更前租金，再发起一笔新变更把租金改回去。
     *
     * <p>用「再发起一笔变更」而非直接改库，是为了保留完整审计链条。
     */
    private String revertRentChange(Long contractId) {
        if (contractId == null || changeMapper == null || contractChangeService == null) {
            return null;
        }
        BizContractChange last = changeMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<BizContractChange>()
                        .eq(BizContractChange::getContractId, contractId)
                        .eq(BizContractChange::getChangeType, "RENT_ADJUST")
                        .eq(BizContractChange::getApproveStatus, "APPROVED")
                        .orderByDesc(BizContractChange::getId)
                        .last("LIMIT 1"));
        if (last == null) {
            return null;
        }
        try {
            @SuppressWarnings("unchecked")
            LinkedHashMap<String, Object> before =
                    JSON.readValue(last.getBeforeJson(), LinkedHashMap.class);
            Object oldRent = before.get("monthlyRent");
            if (oldRent == null) {
                return null;
            }
            BigDecimal rent = new BigDecimal(String.valueOf(oldRent))
                    .setScale(2, java.math.RoundingMode.HALF_UP);
            ChangeVO c = contractChangeService.create(contractId, new ChangeCreateCmd(
                    "RENT_ADJUST", "复议恢复：按原租金标准执行（来源变更单 " + last.getId() + "）",
                    rent, null, null, null, LocalDate.now(),
                    "由申诉单触发的反向调租"));
            contractChangeService.approve(c.id());
            return "租金已恢复为 " + rent + "（反向变更单 " + c.id() + "）";
        } catch (Exception ex) {
            log.warn("复议反向调租失败：{}", ex.getMessage());
            return "反向调租失败（" + ex.getMessage() + "），需人工处理";
        }
    }

    /** 撤销年审自动生成的退租腾退单。 */
    private String cancelAutoTermination(BizAppeal e) {
        if (terminationService == null || reviewMapper == null) {
            return null;
        }
        BizAnnualReview rv = reviewMapper.selectById(e.getBizId());
        if (rv == null || rv.getContractId() == null) {
            return null;
        }
        try {
            var page = terminationService.page(1, 5, null, "APPLYING", rv.getContractId(),
                    null, null);
            if (page.total() == 0) {
                return "无待处理的退租单需撤销";
            }
            TerminationVO t = page.rows().get(0);
            terminationService.cancel(t.id(),
                    "复议（" + e.getAppealNo() + "）异议成立，撤销腾退决定");
            return "已撤销退租单 " + t.terminationNo();
        } catch (Exception ex) {
            log.warn("撤销退租单失败：{}", ex.getMessage());
            return "撤销退租单失败（" + ex.getMessage() + "），需人工处理";
        }
    }

''' + anchor
assert anchor in s
s = s.replace(anchor, helper, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 复议决定已接入原业务回写')
