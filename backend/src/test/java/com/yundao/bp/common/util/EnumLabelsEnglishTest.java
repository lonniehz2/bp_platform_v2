package com.yundao.bp.common.util;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

/** 英文导出标签不得回退中文。 */
class EnumLabelsEnglishTest {

    @Test
    void knownCodes() {
        assertEquals("Public Rental", EnumLabels.ofEnglish("HOUSE_TYPE", "PUBLIC_RENTAL"));
        assertEquals("Vacant", EnumLabels.ofEnglish("HOUSE_STATUS", "VACANT"));
        assertEquals("Available", EnumLabels.ofEnglish("HOUSE_STATUS", "AVAILABLE"));
        assertEquals("Terminated", EnumLabels.ofEnglish("CONTRACT_STATUS", "TERMINATED"));
        assertEquals("Renewing", EnumLabels.ofEnglish("CONTRACT_STATUS", "RENEWING"));
        assertEquals("Unpaid", EnumLabels.ofEnglish("BILL_STATUS", "UNPAID"));
    }

    @Test
    void unknownCodeFallsBackToCodeNotChinese() {
        assertEquals("SOME_NEW_CODE", EnumLabels.ofEnglish("HOUSE_STATUS", "SOME_NEW_CODE"));
    }
}
