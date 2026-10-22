package com.yundao.bp.biz.dto;

/**
 * 公示中签名单中的一条记录。
 *
 * @param personName     中签人姓名
 * @param idCardMask     脱敏身份证号
 * @param phoneMask      脱敏手机号
 * @param houseName      中签房源
 * @param lotterySeq     摇号序号
 * @param selectSeq      选房序号
 * @param resultTypeLabel 结果（中签/候补等）
 */
public record PublicityWinnerVO(
        Long personId,
        String personName,
        String idCardMask,
        String phoneMask,
        String houseName,
        String lotterySeq,
        Integer selectSeq,
        String resultType,
        String resultTypeLabel
) {
}
