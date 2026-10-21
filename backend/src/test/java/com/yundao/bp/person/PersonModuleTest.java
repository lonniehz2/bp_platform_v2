package com.yundao.bp.person;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.person.dto.PersonCreateCmd;
import com.yundao.bp.person.dto.PersonVO;
import com.yundao.bp.person.entity.Person;
import com.yundao.bp.person.mapper.PersonMapper;
import com.yundao.bp.person.service.PersonService;
import com.yundao.bp.person.service.impl.PersonServiceImpl;
import com.yundao.bp.person.util.SensitiveDataCodec;
import java.time.LocalDate;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * person 模块测试。
 *
 * <p>重点覆盖：
 * <ol>
 *   <li><b>敏感数据三列策略</b>（密文/哈希/脱敏）—— 防止明文泄漏到 VO</li>
 *   <li><b>身份证校验位算法</b>（GB 11643-1999）</li>
 *   <li>唯一性校验走哈希列</li>
 *   <li>状态机与删除保护</li>
 * </ol>
 *
 * <p>用 LENIENT 严格度：各用例按需 stub，避免"未使用 stub"误报。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class PersonModuleTest {

    /**
     * 合法 18 位身份证。校验位按 GB 11643 计算：
     * 加权和 167 → 167 % 11 = 2 → 校验码 'X'
     */
    private static final String VALID_ID_CARD = "11010519491231002X";
    /** 校验位被改错（应为 X，写成 1） */
    private static final String BAD_ID_CARD = "110105194912310021";

    @Mock
    private PersonMapper personMapper;

    private PersonService personService;

    @BeforeEach
    void setUp() {
        personService = new PersonServiceImpl(personMapper,
                org.mockito.Mockito.mock(com.yundao.bp.iam.mapper.IamOrgMapper.class),
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        // 默认插入成功（各用例共用；LENIENT 下不会因未用而报错）
        when(personMapper.insert(any(Person.class))).thenReturn(1);
        when(personMapper.updateById(any(Person.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    // ==================== 1. 敏感数据编解码 ====================

    @Test
    @DisplayName("身份证脱敏：保留前 6 后 4")
    void maskIdCard() {
        assertEquals("110105********002X", SensitiveDataCodec.maskIdCard(VALID_ID_CARD));
        // 15 位旧证：保留前 6 后 4，中间 5 个星号
        assertEquals("330106*****1121", SensitiveDataCodec.maskIdCard("330106900101121"));
        assertNull(SensitiveDataCodec.maskIdCard(null));
        assertNotNull(SensitiveDataCodec.maskIdCard("123"));
    }

    @Test
    @DisplayName("手机号脱敏：保留前 3 后 4")
    void maskPhone() {
        assertEquals("138****8000", SensitiveDataCodec.maskPhone("13800138000"));
        assertNull(SensitiveDataCodec.maskPhone(null));
    }

    @Test
    @DisplayName("姓名脱敏：保留首尾")
    void maskName() {
        assertEquals("张", SensitiveDataCodec.maskName("张"));
        assertEquals("张*", SensitiveDataCodec.maskName("张三"));
        assertEquals("张*丰", SensitiveDataCodec.maskName("张三丰"));
        // 5 字名：首 + 3 星 + 尾
        assertEquals("欧***子", SensitiveDataCodec.maskName("欧阳某某子"));
    }

    @Test
    @DisplayName("哈希：确定性（同输入同输出）且不可逆")
    void hashDeterministic() {
        String h1 = SensitiveDataCodec.hash(VALID_ID_CARD);
        String h2 = SensitiveDataCodec.hash(VALID_ID_CARD);
        assertEquals(h1, h2, "同输入必须同输出（用于等值检索）");
        assertEquals(64, h1.length(), "SHA-256 十六进制 64 位");
        assertFalse(h1.contains(VALID_ID_CARD), "哈希不得包含原文");
        assertNotEquals(h1, SensitiveDataCodec.hash(BAD_ID_CARD));
    }

    @Test
    @DisplayName("哈希：不同盐产生不同结果（防彩虹表）")
    void hashSaltMatters() {
        assertNotEquals(SensitiveDataCodec.hash(VALID_ID_CARD, "saltA"),
                SensitiveDataCodec.hash(VALID_ID_CARD, "saltB"));
    }

    // ==================== 2. 校验 ====================

    @Test
    @DisplayName("身份证校验位算法（GB 11643）")
    void idCardChecksum() {
        assertTrue(SensitiveDataCodec.verifyIdCardChecksum(VALID_ID_CARD),
                "11010519491231002X 校验位应通过");
        assertFalse(SensitiveDataCodec.verifyIdCardChecksum(BAD_ID_CARD),
                "校验位错误应被拒绝");
        assertFalse(SensitiveDataCodec.verifyIdCardChecksum("12345"));
        assertFalse(SensitiveDataCodec.verifyIdCardChecksum(null));
    }

    @Test
    @DisplayName("身份证格式校验")
    void idCardFormat() {
        assertTrue(SensitiveDataCodec.isValidIdCard(VALID_ID_CARD));
        assertTrue(SensitiveDataCodec.isValidIdCard("330106900101121"), "15 位旧证");
        assertFalse(SensitiveDataCodec.isValidIdCard("12345"));
        assertFalse(SensitiveDataCodec.isValidIdCard("11010519491231002Y"), "Y 非合法校验码");
        assertFalse(SensitiveDataCodec.isValidIdCard(null));
    }

    @Test
    @DisplayName("手机号校验：第 2 位必须为 3~9")
    void phoneFormat() {
        assertTrue(SensitiveDataCodec.isValidPhone("13800138000"));
        assertTrue(SensitiveDataCodec.isValidPhone("19912345678"));
        // 第 2 位为 2，非有效号段 —— 旧正则 ^1\d{10}$ 会误判为合法
        assertFalse(SensitiveDataCodec.isValidPhone("12345678901"),
                "12345678901 不是合法手机号");
        assertFalse(SensitiveDataCodec.isValidPhone("1380013800"), "10 位应拒绝");
        assertFalse(SensitiveDataCodec.isValidPhone(null));
    }

    @Test
    @DisplayName("从身份证派生生日与性别")
    void deriveFromIdCard() {
        assertEquals(LocalDate.of(1949, 12, 31),
                SensitiveDataCodec.birthdayFromIdCard(VALID_ID_CARD));
        // 第 17 位为 2（偶）→ F
        assertEquals("F", SensitiveDataCodec.genderFromIdCard(VALID_ID_CARD));
        // 第 17 位为 1（奇）→ M
        assertEquals("M", SensitiveDataCodec.genderFromIdCard("110105194912310011"));
        assertEquals("U", SensitiveDataCodec.genderFromIdCard("123"));
    }

    // ==================== 3. 创建人员 ====================

    @Test
    @DisplayName("创建人员：三列策略正确落库")
    void createWritesThreeColumns() {
        when(personMapper.selectCount(any())).thenReturn(0L);

        PersonVO vo = personService.create(new PersonCreateCmd(
                "张三", VALID_ID_CARD, "13800138000", 900000L,
                "URBAN", "MARRIED", "本科", "某公司", null));

        assertEquals("张三", vo.personName());
        assertEquals("110105********002X", vo.idCardMask(), "身份证必须脱敏后返回");
        assertEquals("138****8000", vo.phoneMask(), "手机号必须脱敏后返回");
        assertEquals("F", vo.gender(), "性别应从身份证派生");
        assertEquals(LocalDate.of(1949, 12, 31), vo.birthday(), "生日应从身份证派生");
        assertEquals("UNVERIFIED", vo.verifyStatus());
        assertEquals("NORMAL", vo.personStatus());
        assertNotNull(vo.personCode());
        assertTrue(vo.personCode().startsWith("P"));
    }

    @Test
    @DisplayName("⚠️ VO 绝不返回身份证/手机号原文或哈希")
    void voNeverLeaksPlaintext() {
        when(personMapper.selectCount(any())).thenReturn(0L);
        PersonVO vo = personService.create(new PersonCreateCmd(
                "李四", VALID_ID_CARD, "13800138000", null, null, null, null, null, null));

        String dump = String.valueOf(vo);
        assertFalse(dump.contains(VALID_ID_CARD), "VO 不得含身份证原文");
        assertFalse(dump.contains("13800138000"), "VO 不得含手机号原文");
        assertFalse(dump.contains(SensitiveDataCodec.hash(VALID_ID_CARD)), "VO 不得含哈希");
    }

    @Test
    @DisplayName("身份证被占用（同一哈希）应拒绝")
    void duplicateIdCardRejected() {
        when(personMapper.selectCount(any())).thenReturn(1L);
        BizException ex = assertThrows(BizException.class, () ->
                personService.create(new PersonCreateCmd(
                        "王五", VALID_ID_CARD, null, null, null, null, null, null, null)));
        assertEquals(ErrorCode.DUPLICATED, ex.errorCode());
    }

    @Test
    @DisplayName("校验位错误的身份证应拒绝")
    void badChecksumRejected() {
        BizException ex = assertThrows(BizException.class, () ->
                personService.create(new PersonCreateCmd(
                        "赵六", BAD_ID_CARD, null, null, null, null, null, null, null)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("校验位"));
    }

    @Test
    @DisplayName("格式错误的手机号应拒绝")
    void badPhoneRejected() {
        BizException ex = assertThrows(BizException.class, () ->
                personService.create(new PersonCreateCmd(
                        "钱七", null, "12345", null, null, null, null, null, null)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("无身份证/手机号也可建档（如手工录入的儿童）")
    void createWithoutSensitiveFields() {
        PersonVO vo = personService.create(new PersonCreateCmd(
                "孙八", null, null, null, null, null, null, null, "手工录入"));
        assertEquals("孙八", vo.personName());
        assertNull(vo.idCardMask());
        assertNull(vo.phoneMask());
        assertEquals("UNVERIFIED", vo.verifyStatus());
    }

    @Test
    @DisplayName("无租户上下文时拒绝创建（安全底线）")
    void noTenantRejected() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, () ->
                personService.create(new PersonCreateCmd(
                        "X", null, null, null, null, null, null, null, null)));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 4. 状态与删除 ====================

    @Test
    @DisplayName("状态迁移：NORMAL → BLACKLIST 合法")
    void changeStatusValid() {
        Person p = new Person();
        p.setId(1L);
        p.setPersonStatus("NORMAL");
        p.setPersonName("张三");
        when(personMapper.selectById(1L)).thenReturn(p);

        assertEquals("BLACKLIST", personService.changeStatus(1L, "BLACKLIST").personStatus());
    }

    @Test
    @DisplayName("非法状态值应拒绝")
    void changeStatusInvalid() {
        BizException ex = assertThrows(BizException.class,
                () -> personService.changeStatus(1L, "WHATEVER"));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("已注销人员不允许再改状态")
    void cancelledCannotChange() {
        Person p = new Person();
        p.setId(1L);
        p.setPersonStatus("CANCELLED");
        when(personMapper.selectById(1L)).thenReturn(p);

        BizException ex = assertThrows(BizException.class,
                () -> personService.changeStatus(1L, "NORMAL"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("黑名单人员不允许删除")
    void blacklistCannotDelete() {
        Person p = new Person();
        p.setId(1L);
        p.setPersonStatus("BLACKLIST");
        when(personMapper.selectById(1L)).thenReturn(p);

        BizException ex = assertThrows(BizException.class, () -> personService.delete(1L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("黑名单"));
    }

    @Test
    @DisplayName("按身份证查找（走哈希列）")
    void findByIdCardUsesHash() {
        Person p = new Person();
        p.setId(1L);
        p.setPersonName("张三");
        p.setIdCardMask("110105********002X");
        when(personMapper.selectOne(any())).thenReturn(p);

        PersonVO vo = personService.findByIdCard(VALID_ID_CARD);
        assertNotNull(vo);
        assertEquals("110105********002X", vo.idCardMask());
    }

    @Test
    @DisplayName("按身份证查找不存在时返回 null（不抛异常）")
    void findByIdCardNotFound() {
        when(personMapper.selectOne(any())).thenReturn(null);
        assertNull(personService.findByIdCard(VALID_ID_CARD));
    }
}
