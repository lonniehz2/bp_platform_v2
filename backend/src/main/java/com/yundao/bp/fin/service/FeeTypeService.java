package com.yundao.bp.fin.service;

import com.yundao.bp.fin.entity.FinFeeType;
import java.util.List;

/** 费用类型字典。 */
public interface FeeTypeService {

    List<FinFeeType> list(boolean enabledOnly);

    FinFeeType create(String code, String name, Integer sortNo);

    FinFeeType update(Long id, String code, String name, Integer sortNo);

    FinFeeType setStatus(Long id, boolean enabled);
}
