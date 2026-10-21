# -*- coding: utf-8 -*-
"""年审 EXIT → 自动发起退租腾退单 + 过渡期可显式指定"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ==================== 1. 修正：过渡期可显式指定（不限类型）====================
p1 = os.path.join(BASE, r'biz\service\impl\TerminationServiceImpl.java')
s1 = io.open(p1, encoding='utf-8').read()

old_cond = '''        // 重庆：腾退过渡期（仅腾退类给过渡期）
        if (type == TerminationType.EXPEL || type == TerminationType.NORMAL) {'''
new_cond = '''        // 重庆：腾退过渡期。
        // 除腾退类（EXPEL/NORMAL）默认给过渡期外，
        // 显式传入 transitionMonths 时（如年审退出）也一律生效，
        // 避免"年审超标退出"这类政策性退出拿不到过渡期。
        if (type == TerminationType.EXPEL || type == TerminationType.NORMAL
                || cmd.transitionMonths() != null) {'''
if old_cond in s1:
    s1 = s1.replace(old_cond, new_cond, 1)
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ✓ 过渡期支持显式指定（不限退租类型）')
else:
    print('  - 过渡期条件未匹配（可能已改）')

# ==================== 2. 年审 EXIT → 自动生成腾退单 ====================
p2 = os.path.join(BASE, r'biz\service\impl\AnnualReviewServiceImpl.java')
s2 = io.open(p2, encoding='utf-8').read()

if 'terminationService' in s2:
    print('已接入，跳过')
    raise SystemExit

# import
s2 = s2.replace('import com.yundao.bp.biz.service.AnnualReviewService;',
                'import com.yundao.bp.biz.dto.TerminationCreateCmd;\n'
                'import com.yundao.bp.biz.dto.TerminationVO;\n'
                'import com.yundao.bp.biz.service.AnnualReviewService;\n'
                'import com.yundao.bp.biz.service.TerminationService;', 1)

# 字段（可选注入，避免影响既有构造器与单测）
s2 = s2.replace('''    private final SnowflakeIdGenerator idGen;

    public AnnualReviewServiceImpl(''',
                '''    private final SnowflakeIdGenerator idGen;
    /** 退租腾退服务（年审结论 EXIT 时自动发起腾退单） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private TerminationService terminationService;

    public AnnualReviewServiceImpl(''', 1)

# finish() 里：EXIT 时自动发起腾退
old_finish = '''        log.info("复核单 {} 完成：{}（{}）下次复核 {}",
                e.getReviewNo(), rr.label(), e.getReviewYear(), next);
        return ReviewVO.from(e);'''
new_finish = '''        // ⭐ 年审结论 EXIT → 自动发起退租腾退单（决策 D25）
        // 否则年审只是"写了句结论"，房源和授权都不会动
        if (rr == ReviewResult.EXIT && e.getContractId() != null) {
            autoCreateTermination(e);
        }

        log.info("复核单 {} 完成：{}（{}）下次复核 {}",
                e.getReviewNo(), rr.label(), e.getReviewYear(), next);
        return ReviewVO.from(e);'''
assert old_finish in s2, 'finish 出口锚点缺失'
s2 = s2.replace(old_finish, new_finish, 1)

# 新增私方法
anchor = '''    // ==================== 内部 ===================='''
helper = '''    /**
     * 年审结论 EXIT → 自动发起退租腾退单。
     *
     * <p><b>幂等</b>：该合同已有退租单则跳过，避免重复发起。
     *
     * <p><b>政策</b>：年审退出属政策性退出（非违规），
     * 退租类型用 {@code OTHER}（不能用 EXPEL，否则会误触发 5 年禁申），
     * 并给 3 个月腾退过渡期。
     */
    private void autoCreateTermination(BizAnnualReview rv) {
        if (terminationService == null) {
            log.warn("退租服务不可用，年审 {} 的 EXIT 结论未自动发起腾退单", rv.getReviewNo());
            return;
        }
        try {
            // 幂等：已有退租单则不再发起
            var existing = terminationService.page(1, 1, null, null, rv.getContractId(), null, null);
            if (existing.total() > 0) {
                log.info("合同 {} 已有退租单，年审 {} 不重复发起", rv.getContractId(),
                        rv.getReviewNo());
                return;
            }
            LocalDate planExit = LocalDate.now().plusMonths(3);
            String reason = "年审复核不再符合保障条件（复核单 " + rv.getReviewNo() + "）"
                    + (rv.getAdjustContent() == null ? "" : "：" + rv.getAdjustContent());
            TerminationVO t = terminationService.apply(new TerminationCreateCmd(
                    rv.getContractId(), rv.getHouseId(), rv.getPersonId(),
                    "OTHER", planExit, reason,
                    3, new java.math.BigDecimal("1.5"), null));

            // 回写年审单，便于追溯
            String old = rv.getAdjustContent() == null ? "" : rv.getAdjustContent();
            rv.setAdjustContent(old + "｜已自动发起退租单 " + t.terminationNo());
            rv.setUpdateTime(LocalDateTime.now());
            mapper.updateById(rv);
            log.info("⭐⭐ 年审 {} 结论 EXIT → 已自动发起退租单 {}（计划退房 {}）",
                    rv.getReviewNo(), t.terminationNo(), planExit);
        } catch (Exception ex) {
            // 自动发起失败不能回滚年审结论（结论本身是有效的），仅记录待人工处理
            log.error("年审 {} 自动发起退租单失败，需人工处理：{}", rv.getReviewNo(),
                    ex.getMessage());
        }
    }

''' + anchor
assert anchor in s2
s2 = s2.replace(anchor, helper, 1)

io.open(p2, 'w', encoding='utf-8').write(s2)
print('  ✓ 年审 EXIT 已接入自动发起腾退单')
