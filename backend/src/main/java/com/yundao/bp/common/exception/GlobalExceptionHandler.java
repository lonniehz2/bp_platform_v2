package com.yundao.bp.common.exception;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.R;
import jakarta.servlet.http.HttpServletRequest;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

/**
 * 全局异常处理：把各类异常统一收敛为 {@link R}。
 *
 * <p><b>安全要求</b>：不向客户端泄露堆栈与内部实现细节；完整堆栈只进日志。
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * 解包 MyBatis / Spring 包装的异常，向上找到 {@link BizException}。
     *
     * <p><b>为什么必须这么做</b>：多租户插件在 MyBatis 拦截器内部调用
     * {@code TenantContext.tenantId()}，该处抛出的 {@code BizException}
     * 会被 MyBatis 包装成 {@code MyBatisSystemException}。
     * 若不还原，客户端会收到 {@code BP99999}，掩盖“租户上下文缺失/越权”这类
     * 关键安全语义，也不利于排障。
     */
    private BizException findBiz(Throwable e) {
        Throwable cur = e;
        int guard = 0;
        while (cur != null && guard++ < 12) {
            if (cur instanceof BizException be) {
                return be;
            }
            cur = cur.getCause();
        }
        return null;
    }

    @ExceptionHandler(BizException.class)
    public ResponseEntity<R<Void>> handleBiz(BizException e, HttpServletRequest req) {
        log.warn("业务异常 [{}] {} {} - {}", e.errorCode().code(), req.getMethod(),
                req.getRequestURI(), e.getMessage());
        return ResponseEntity.status(e.errorCode().httpStatus()).body(R.fail(e.errorCode(), e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<R<Void>> handleValid(MethodArgumentNotValidException e) {
        String detail = e.getBindingResult().getFieldErrors().stream()
                .map(this::fmtFieldError)
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(ErrorCode.PARAM_INVALID.httpStatus())
                .body(R.fail(ErrorCode.PARAM_INVALID, detail));
    }

    @ExceptionHandler(BindException.class)
    public ResponseEntity<R<Void>> handleBind(BindException e) {
        String detail = e.getFieldErrors().stream()
                .map(this::fmtFieldError)
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(ErrorCode.PARAM_INVALID.httpStatus())
                .body(R.fail(ErrorCode.PARAM_INVALID, detail));
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<R<Void>> handleMissingParam(MissingServletRequestParameterException e) {
        return ResponseEntity.status(ErrorCode.PARAM_MISSING.httpStatus())
                .body(R.fail(ErrorCode.PARAM_MISSING, "缺少参数: " + e.getParameterName()));
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<R<Void>> handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        return ResponseEntity.status(ErrorCode.PARAM_INVALID.httpStatus())
                .body(R.fail(ErrorCode.PARAM_INVALID, "参数类型错误: " + e.getName()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<R<Void>> handleIllegalArg(IllegalArgumentException e) {
        return ResponseEntity.status(ErrorCode.PARAM_INVALID.httpStatus())
                .body(R.fail(ErrorCode.PARAM_INVALID, e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<R<Void>> handleOther(Exception e, HttpServletRequest req) {
        // 先尝试从嵌套异常中还原业务异常（如 MyBatis 包装的租户上下文缺失）
        BizException biz = findBiz(e);
        if (biz != null) {
            log.warn("业务异常(解包) [{}] {} {} - {}", biz.errorCode().code(),
                    req.getMethod(), req.getRequestURI(), biz.getMessage());
            return ResponseEntity.status(biz.errorCode().httpStatus())
                    .body(R.fail(biz.errorCode(), biz.getMessage()));
        }
        log.error("未处理异常 {} {}", req.getMethod(), req.getRequestURI(), e);
        return ResponseEntity.status(ErrorCode.SYSTEM_ERROR.httpStatus())
                .body(R.fail(ErrorCode.SYSTEM_ERROR));
    }

    private String fmtFieldError(FieldError fe) {
        return fe.getField() + ": " + fe.getDefaultMessage();
    }
}
