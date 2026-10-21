# -*- coding: utf-8 -*-
"""修复：恢复被覆盖的 ReviewResult（审核结果），新枚举改名 AnnualReviewResult"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) 恢复审查结果枚举
restored = '''package com.yundao.bp.biz.constant;

/**
 * 审核结果（对应 {@code bp_biz_review_record.review_result}）。
 *
 * <p>注意：年审（复核）结果用的是另一个枚举
 * {@link AnnualReviewResult}（KEEP/ADJUST/EXIT/PENDING），两者不可混用。
 */
public enum ReviewResult {

    PASS("通过"),
    REJECT("不通过"),
    SUPPLEMENT("需补件");

    private final String label;

    ReviewResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否通过。 */
    public boolean isPass() {
        return this == PASS;
    }
}
'''
p1 = os.path.join(BASE, r'biz\constant\ReviewResult.java')
io.open(p1, 'w', encoding='utf-8').write(restored)
print('  ✓ 已恢复 ReviewResult（PASS/REJECT/SUPPLEMENT）')

# 2) 新建 AnnualReviewResult
annual = '''package com.yundao.bp.biz.constant;

/**
 * 年审（复核）结果（对应 {@code bp_biz_annual_review.review_result}）。
 *
 * <p>与审核结果 {@link ReviewResult} 区分：本枚举表达"保障资格"的复核结论。
 */
public enum AnnualReviewResult {

    KEEP("保留资格"),
    ADJUST("调整（租金/房源）"),
    EXIT("退出"),
    PENDING("待定");

    private final String label;

    AnnualReviewResult(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要后续处置（调整或退出）。 */
    public boolean needsAction() {
        return this == ADJUST || this == EXIT;
    }
}
'''
p2 = os.path.join(BASE, r'biz\constant\AnnualReviewResult.java')
io.open(p2, 'w', encoding='utf-8').write(annual)
print('  ✓ 新增 AnnualReviewResult（KEEP/ADJUST/EXIT/PENDING）')

# 3) 改引用（仅年审相关文件）
for rel in (r'biz\service\impl\AnnualReviewServiceImpl.java', r'biz\dto\ReviewVO.java'):
    path = os.path.join(BASE, rel)
    s = io.open(path, encoding='utf-8').read()
    s = s.replace('import com.yundao.bp.biz.constant.ReviewResult;',
                  'import com.yundao.bp.biz.constant.AnnualReviewResult;')
    s = s.replace('ReviewResult.valueOf(', 'AnnualReviewResult.valueOf(')
    s = s.replace('ReviewResult rr;', 'AnnualReviewResult rr;')
    io.open(path, 'w', encoding='utf-8').write(s)
    print('  ✓ 改引用: %s' % os.path.basename(path))
