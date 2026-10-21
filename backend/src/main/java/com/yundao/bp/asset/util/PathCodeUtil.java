package com.yundao.bp.asset.util;

/**
 * 编码规则工具：{@code path_code}（展示与排序）与 {@code space_path}（祖先 ID 链）。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §24（地址与路径编码规则）。
 *
 * <p><b>path_code 规则</b>：每级 2 位序号，用 {@code /} 分隔，<b>以 / 结尾</b>。
 * <pre>
 *   01/          片区A
 *   01/01/       楼栋1
 *   01/01/02/    单元2
 *   01/01/02/05/ 楼层5
 * </pre>
 *
 * <p><b>为什么必须带结尾 /</b>：保证前缀查询 {@code LIKE '01/01/%'} 不会误匹配 {@code 01/011/}。
 *
 * <p><b>与 space_path 的区别</b>：space_path 存祖先 ID 链（用于 join 查父节点），
 * path_code 存编码链（用于展示与排序）。两者并存、职责不同。
 */
public final class PathCodeUtil {

    /** 每级位数（2 位支持 99 个子节点；大型小区可改 3 位，但需全局一致） */
    public static final int SEG_WIDTH = 2;
    private static final int MAX_CHILD = (int) Math.pow(10, SEG_WIDTH) - 1;

    private PathCodeUtil() {
    }

    /**
     * 生成 path_code。
     *
     * @param parentPathCode 父节点 path_code（顶级传 null 或空）
     * @param seq            本级序号（1..MAX_CHILD）
     */
    public static String build(String parentPathCode, int seq) {
        if (seq < 1 || seq > MAX_CHILD) {
            throw new IllegalArgumentException(
                    "同级序号必须在 1~" + MAX_CHILD + "，实际 " + seq + "（如需更多请调整 SEG_WIDTH）");
        }
        String prefix = (parentPathCode == null || parentPathCode.isBlank()) ? "" : parentPathCode;
        if (!prefix.isEmpty() && !prefix.endsWith("/")) {
            prefix = prefix + "/";
        }
        return prefix + String.format("%0" + SEG_WIDTH + "d", seq) + "/";
    }

    /** 生成 space_path（祖先 ID 链，以 / 结尾）。 */
    public static String buildSpacePath(String parentSpacePath, Long parentId) {
        if (parentId == null) {
            return "";
        }
        String prefix = (parentSpacePath == null) ? "" : parentSpacePath;
        if (!prefix.isEmpty() && !prefix.endsWith("/")) {
            prefix = prefix + "/";
        }
        return prefix + parentId + "/";
    }

    /** 前缀查询条件（配合 LIKE 使用，如 {@code "01/01/%"}）。 */
    public static String prefixPattern(String pathCode) {
        if (pathCode == null || pathCode.isBlank()) {
            return "%";
        }
        return pathCode.endsWith("/") ? pathCode + "%" : pathCode + "/%";
    }

    /** 解析路径深度（如 {@code "01/01/02/"} → 3）。 */
    public static int depth(String pathCode) {
        if (pathCode == null || pathCode.isBlank()) {
            return 0;
        }
        int n = 0;
        for (int i = 0; i < pathCode.length(); i++) {
            if (pathCode.charAt(i) == '/') {
                n++;
            }
        }
        return n;
    }
}
