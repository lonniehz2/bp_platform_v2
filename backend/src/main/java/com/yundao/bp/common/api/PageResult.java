package com.yundao.bp.common.api;

import java.io.Serializable;
import java.util.List;

/**
 * 分页结果。
 *
 * @param <T> 行类型
 */
public record PageResult<T>(long total, long pageNum, long pageSize, List<T> rows) implements Serializable {

    public static <T> PageResult<T> of(long total, long pageNum, long pageSize, List<T> rows) {
        return new PageResult<>(total, pageNum, pageSize, rows == null ? List.of() : rows);
    }

    public static <T> PageResult<T> empty(long pageNum, long pageSize) {
        return new PageResult<>(0, pageNum, pageSize, List.of());
    }
}
