package com.yundao.bp.common.id;

/**
 * 雪花 ID 生成器（64 位，单调递增趋势友好）。
 *
 * <p>设计依据：DDL 中主键均为 {@code BIGINT UNSIGNED NOT NULL} 且<b>无 AUTO_INCREMENT</b>，
 * 主键由应用层生成。
 *
 * <p>结构：{@code 1 位符号(0) | 41 位时间戳(毫秒) | 5 位数据中心 | 5 位机器 | 12 位序列}
 * <ul>
 *   <li>41 位毫秒 ≈ 69 年</li>
 *   <li>单节点每毫秒最多 4096 个 ID</li>
 * </ul>
 *
 * <p>⚠️ <b>前端注意</b>：ID 超过 JS 安全整数上限（2^53），
 * 因此 JSON 序列化时必须转为字符串（见 {@code JacksonConfig}）。
 */
public final class SnowflakeIdGenerator {

    private static final long EPOCH = 1704067200000L;      // 2024-01-01 00:00:00 UTC
    private static final long WORKER_BITS = 5L;
    private static final long DATACENTER_BITS = 5L;
    private static final long SEQUENCE_BITS = 12L;

    private static final long MAX_WORKER = ~(-1L << WORKER_BITS);         // 31
    private static final long MAX_DATACENTER = ~(-1L << DATACENTER_BITS); // 31
    private static final long SEQUENCE_MASK = ~(-1L << SEQUENCE_BITS);    // 4095

    private static final long WORKER_SHIFT = SEQUENCE_BITS;
    private static final long DATACENTER_SHIFT = SEQUENCE_BITS + WORKER_BITS;
    private static final long TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_BITS + DATACENTER_BITS;

    private final long workerId;
    private final long datacenterId;

    private long sequence = 0L;
    private long lastTimestamp = -1L;

    public SnowflakeIdGenerator(long datacenterId, long workerId) {
        if (workerId < 0 || workerId > MAX_WORKER) {
            throw new IllegalArgumentException("workerId 必须在 0~" + MAX_WORKER);
        }
        if (datacenterId < 0 || datacenterId > MAX_DATACENTER) {
            throw new IllegalArgumentException("datacenterId 必须在 0~" + MAX_DATACENTER);
        }
        this.workerId = workerId;
        this.datacenterId = datacenterId;
    }

    /** 生成下一个 ID（线程安全）。 */
    public synchronized long nextId() {
        long ts = System.currentTimeMillis();
        if (ts < lastTimestamp) {
            // 时钟回拨：小幅度等待，大幅度直接报错（避免生成重复 ID）
            long offset = lastTimestamp - ts;
            if (offset <= 5) {
                ts = waitUntil(lastTimestamp);
            } else {
                throw new IllegalStateException("时钟回拨 " + offset + "ms，拒绝生成 ID");
            }
        }
        if (ts == lastTimestamp) {
            sequence = (sequence + 1) & SEQUENCE_MASK;
            if (sequence == 0) {
                ts = waitUntil(lastTimestamp + 1);
            }
        } else {
            sequence = 0L;
        }
        lastTimestamp = ts;
        return ((ts - EPOCH) << TIMESTAMP_SHIFT)
                | (datacenterId << DATACENTER_SHIFT)
                | (workerId << WORKER_SHIFT)
                | sequence;
    }

    /** 生成字符串形式（可直接用于 JSON 传输，规避 JS 精度丢失）。 */
    public String nextIdStr() {
        return Long.toString(nextId());
    }

    private long waitUntil(long target) {
        long ts = System.currentTimeMillis();
        while (ts < target) {
            ts = System.currentTimeMillis();
        }
        return ts;
    }
}
