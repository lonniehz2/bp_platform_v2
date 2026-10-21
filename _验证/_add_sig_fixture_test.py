# -*- coding: utf-8 -*-
"""追加跨语言签名一致性测试到 OpenSignTest"""
import io

p = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\open'
     r'\OpenSignTest.java')
s = io.open(p, encoding='utf-8').read()

if 'FIXTURE_SIGN' in s:
    print('已存在，跳过')
else:
    anchor = '''    @Test
    @DisplayName("生成的 AppKey / AppSecret 格式与长度")'''
    block = '''    // ==================== 跨语言契约 ====================

    /**
     * ⭐⭐ 与 Python 客户端算出的签名必须完全一致。
     *
     * <p>这个常量由 `_验证/_sig_fixture.py` 用 hmac+hashlib 独立算出。
     * 两边不一致意味着<b>所有第三方调用都会验签失败</b>，
     * 而这种错误在单元测试里发现不了，只能靠固定向量锁住。
     */
    private static final String FIXTURE_SIGN =
            "bfd8aaf613b8ebad85623b253b49e2eb7e7fa1b241412ec44a1e04e793de7f61";

    @Test
    @DisplayName("⭐⭐ 签名与 Python 客户端结果一致（跨语言契约）")
    void crossLanguageFixture() {
        String payload = signer.buildPayload("POST", "/open/house.list",
                "1700000000000", "abc123", "{\\"pageNum\\":1}");
        assertEquals("POST\\n/open/house.list\\n1700000000000\\nabc123\\n{\\"pageNum\\":1}",
                payload, "待签串格式必须与文档一致");
        assertEquals(FIXTURE_SIGN, signer.sign("unit-test-secret", payload),
                "与 Python hmac 结果不一致，第三方将全部验签失败");
    }

''' + anchor
    assert anchor in s
    s = s.replace(anchor, block, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('已追加跨语言签名一致性测试')
