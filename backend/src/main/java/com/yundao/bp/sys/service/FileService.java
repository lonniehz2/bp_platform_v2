package com.yundao.bp.sys.service;

import com.yundao.bp.sys.entity.SysFile;
import java.io.InputStream;
import java.util.List;
import org.springframework.web.multipart.MultipartFile;

/**
 * 附件服务。
 *
 * <p><b>安全约束</b>（缺一不可）：
 * <ol>
 *   <li>扩展名白名单：只允许图片与 PDF（防上传 jsp/exe）</li>
 *   <li>大小上限：默认 10MB</li>
 *   <li>文件名重写为 UUID 存储键：<b>不信任用户文件名</b>，防目录穿越</li>
 *   <li>按租户 + 业务单据隔离查询</li>
 * </ol>
 */
public interface FileService {

    SysFile upload(MultipartFile file, String bizType, Long bizId,
                   Long uploaderId, String uploaderName);

    SysFile get(Long id);

    /** 取文件流（用于下载/预览）。 */
    InputStream openStream(Long id);

    List<SysFile> listByBiz(String bizType, Long bizId);

    /** 逻辑删除。 */
    void remove(Long id);
}
