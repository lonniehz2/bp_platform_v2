package com.yundao.bp.iot.tool;

import com.yundao.bp.iot.legacy.AesCbcStrategy;
import com.yundao.bp.iot.legacy.Md5Signer;
import com.yundao.bp.iot.legacy.YmdClient;
import com.yundao.bp.iot.legacy.YmdToken;
import com.yundao.bp.iot.legacy.dto.YmdLockInfo;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * YmdLegacyVerify —— IoT 现网协议（AES/MD5）连通性验证工具。
 *
 * <p>用途：
 * <ol>
 *   <li><b>自测</b>：验证 AES/MD5 与官方文档示例一致（离线，无需网络）</li>
 *   <li><b>真实调用</b>：取 token、查门锁清单、输出统计（需网络与凭证）</li>
 * </ol>
 *
 * <p>用法：
 * <pre>
 *   # 离线自测（算法是否与官方一致）
 *   java ... YmdLegacyVerify selftest
 *
 *   # 真实调用（凭证用环境变量，避免泄漏到命令行历史）
 *   set YMD_APP_KEY=...      &amp; set YMD_APP_SECRET=...  &amp; set YMD_AGENT_CODE=...
 *   java ... YmdLegacyVerify live
 * </pre>
 */
public final class YmdLegacyVerify {

    private static final String DEFAULT_BASE = "https://api.hzbit.cn:4443";

    public static void main(String[] args) {
        String cmd = args.length > 0 ? args[0] : "help";
        int code;
        switch (cmd) {
            case "selftest" -> code = selftest() ? 0 : 1;
            case "live" -> code = live() ? 0 : 1;
            default -> {
                System.out.println(usage());
                code = 2;
            }
        }
        System.exit(code);
    }

    private static String usage() {
        return """
YmdLegacyVerify —— IoT 现网协议验证（AES/MD5）

  selftest   离线自测：AES/MD5 是否与官方文档示例一致
  live       真实调用：取 token + 查门锁清单（需环境变量 YMD_APP_KEY / YMD_APP_SECRET / YMD_AGENT_CODE）
""";
    }

    // ==================== 离线自测 ====================

    static boolean selftest() {
        int pass = 0, fail = 0;
        System.out.println("==================================================");
        System.out.println(" IoT 现网协议自测（AES/MD5）");
        System.out.println("==================================================");
        System.out.println();

        // 1) AES 文档示例
        String pwd = "5x41nO+EIYENqlj8FmG2XGXMa";
        String plain = "719B29DB1EF45F00D9C5CD320DAE6";
        String expectCt = "FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo=";
        String gotCt = AesCbcStrategy.encrypt(pwd, plain);
        pass += check("AES 加密 = 官方文档示例", expectCt, gotCt);
        pass += check("AES 解密还原明文", plain, AesCbcStrategy.decrypt(pwd, expectCt));

        // 2) 密钥派生
        pass += check("PBKDF2 密钥（16 字节）", "3FA50AED662483A899B22A4BDBF7DE26",
                java.util.HexFormat.of().withUpperCase().formatHex(AesCbcStrategy.deriveKeyBytes(pwd)));

        // 3) MD5 文档示例
        Map<String, String> p = new HashMap<>();
        p.put("loginname", "t4nU902RvhliiPlMMcrzWw==");
        p.put("logpwd", "oFbqQ8bx8KvkHCI/Q2Kaxw==");
        p.put("time", "1553595995");
        p.put("version", "1.0.0");
        pass += check("MD5 签名 = 官方文档示例", "46812299FB1BC111AC69A27F99068BE2", Md5Signer.sign(p));

        // 4) 往返
        String rt = AesCbcStrategy.decrypt(pwd, AesCbcStrategy.encrypt(pwd, "中文测试 abc123"));
        pass += check("AES 中文往返", "中文测试 abc123", rt);

        System.out.println();
        System.out.println("--------------------------------------------------");
        System.out.printf(" 通过项 %d%s%n", pass,
                fail == 0 ? "，全部通过 ✔" : "，存在失败 ✘");
        System.out.println("--------------------------------------------------");
        return fail == 0;
    }

    private static int check(String name, String expect, String actual) {
        boolean ok = expect.equals(actual);
        System.out.printf("  [%s] %-34s %s%n", ok ? "PASS" : "FAIL", name,
                ok ? "" : ("期望=" + brief(expect) + " 实际=" + brief(actual)));
        if (!ok) {
            failures++;
        }
        return ok ? 1 : 0;
    }

    private static int failures = 0;

    private static String brief(String s) {
        if (s == null) {
            return "null";
        }
        return s.length() > 46 ? s.substring(0, 46) + "..." : s;
    }

    // ==================== 真实调用 ====================

    static boolean live() {
        String appKey = env("YMD_APP_KEY");
        String appSecret = env("YMD_APP_SECRET");
        String agentCode = env("YMD_AGENT_CODE");
        String base = env("YMD_BASE_URL", DEFAULT_BASE);

        if (appKey == null || appSecret == null || agentCode == null) {
            System.out.println("缺少环境变量：YMD_APP_KEY / YMD_APP_SECRET / YMD_AGENT_CODE");
            return false;
        }

        System.out.println("==================================================");
        System.out.println(" IoT 真实调用验证");
        System.out.println("==================================================");
        System.out.printf("  baseUrl   = %s%n", base);
        System.out.printf("  appKey    = %s%n", mask(appKey));
        System.out.printf("  agentCode = %s%n", agentCode);
        System.out.println();

        try {
            YmdClient client = YmdClient.create(base, appKey, appSecret, true, true);

            System.out.println("--- 步骤 1：获取 Token ---");
            YmdToken t = client.token();
            System.out.printf("  token    = %s...%n", t.token().substring(0, 24));
            System.out.printf("  pwd      = %s%n", t.pwd());
            System.out.printf("  key      = %s%n",
                    java.util.HexFormat.of().withUpperCase().formatHex(
                            AesCbcStrategy.deriveKeyBytes(t.pwd())));
            System.out.printf("  expiresAt= %s%n", t.expiresAt());

            System.out.println();
            System.out.println("--- 步骤 2：查询代理商门锁清单 ---");
            List<YmdLockInfo> locks = client.listAgentLocks(agentCode);
            System.out.printf("  门锁总数 = %d%n", locks.size());

            if (!locks.isEmpty()) {
                long online = locks.stream().filter(YmdLockInfo::online).count();
                long withBattery = locks.stream().filter(l -> l.batteryPercent() != null).count();
                System.out.printf("  在线     = %d (%.1f%%)%n", online,
                        locks.size() == 0 ? 0.0 : 100.0 * online / locks.size());
                System.out.printf("  有电量信息 = %d 台%n", withBattery);
                System.out.println();
                System.out.println("  前 5 条：");
                locks.stream().limit(5).forEach(l -> System.out.printf(
                        "    %-30s online=%-3s battery=%-6s name=%s%n",
                        brief(l.getLockId()), l.getOnlineStatus(), l.getBattery(), l.getLockName()));
            }
            System.out.println();
            System.out.println("结果：✔ 现网协议打通");
            return true;
        } catch (Exception e) {
            System.out.println("结果：✘ 失败 - " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    private static String env(String name) {
        return env(name, null);
    }

    private static String env(String name, String def) {
        String v = System.getenv(name);
        return (v == null || v.isBlank()) ? def : v;
    }

    private static String mask(String s) {
        return s == null ? "" : (s.length() <= 8 ? "***" : s.substring(0, 8) + "***");
    }
}
