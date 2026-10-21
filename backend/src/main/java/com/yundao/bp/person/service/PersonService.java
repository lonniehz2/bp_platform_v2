package com.yundao.bp.person.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.person.dto.PersonCreateCmd;
import com.yundao.bp.person.dto.PersonVO;

/**
 * 人员服务。
 */
public interface PersonService {

    /** 创建人员（自动：编码生成、身份证哈希/脱敏、手机号哈希）。 */
    PersonVO create(PersonCreateCmd cmd);

    PersonVO get(Long id);

    /** 分页查询（支持姓名模糊、组织、状态过滤）。 */
    PageResult<PersonVO> page(long pageNum, long pageSize, String keyword,
                              Long orgId, String personStatus, Boolean includeChildren);

    /** 按身份证号精确查找（走哈希列，不比对密文）。 */
    PersonVO findByIdCard(String idCard);

    /** 更新人员状态：NORMAL / BLACKLIST / CANCELLED。 */
    /** 修改人员基本信息（不含身份证号） */
    PersonVO update(Long id, com.yundao.bp.person.dto.PersonUpdateCmd cmd);

    PersonVO changeStatus(Long id, String targetStatus);

    void delete(Long id);
}
