package com.yundao.bp.sys.constant;

/**
 * 政策参数键（统一管理，避免散落各处的硬编码）。
 *
 * <p>所有键都支持分租户覆盖，实现「不同地区不同政策」。
 */
public final class ConfigKeys {

    private ConfigKeys() {
    }

    // ---------- 公示 ----------
    /** 配租公示最短自然日（默认 7） */
    public static final String PUBLICITY_ALLOC_MIN_DAYS = "biz.publicity.allocation.minDays";
    /** 资格公示最短自然日（默认 5） */
    public static final String PUBLICITY_QUALIFY_MIN_DAYS = "biz.publicity.qualify.minDays";

    // ---------- 信用惩戒 ----------
    /** 严重违规限制申请年限（默认 5） */
    public static final String CREDIT_BAN_YEARS_SEVERE = "biz.credit.banYears.severe";
    /** 一般违规限制申请年限（默认 1） */
    public static final String CREDIT_BAN_YEARS_NORMAL = "biz.credit.banYears.normal";

    // ---------- 腾退 ----------
    /** 腾退过渡期月数（重庆默认 3） */
    public static final String TERMINATION_TRANSITION_MONTHS = "biz.termination.transition.months";
    /** 过渡期租金倍率（重庆默认 1.5） */
    public static final String TERMINATION_TRANSITION_MULTIPLIER =
            "biz.termination.transition.multiplier";
    /** 搬迁期最大月数（成都默认 6） */
    public static final String TERMINATION_RELOCATION_MAX_MONTHS =
            "biz.termination.relocation.maxMonths";

    // ---------- 配租 ----------
    /** 同一租期最大换房次数（成都默认 1） */
    public static final String EXCHANGE_MAX_TIMES = "biz.exchange.maxTimes";
    /** 应换不换加价倍率（重庆默认 1.5） */
    public static final String EXCHANGE_NO_EXCHANGE_MULTIPLIER =
            "biz.exchange.noExchange.multiplier";
    /** 配租房源冻定时长（小时，默认 72） */
    public static final String ALLOCATION_LOCK_HOURS = "biz.allocation.lockHours";

    // ---------- 年审 ----------
    /** 年审逾期天数阈值（默认 0 = 当年内） */
    public static final String REVIEW_OVERDUE_DAYS = "biz.review.overdue.days";

    // ---------- 申请 ----------
    /** 是否要求实名认证后才能申请（默认 true） */
    public static final String APPLY_REQUIRE_VERIFY = "biz.apply.requireVerify";

    // ---------- 申诉 ----------
    /** 申诉期限自然日（默认 10） */
    public static final String APPEAL_DEADLINE_DAYS = "biz.appeal.deadlineDays";
}
