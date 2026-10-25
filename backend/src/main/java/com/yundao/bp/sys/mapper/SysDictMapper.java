package com.yundao.bp.sys.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.sys.entity.SysDict;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SysDictMapper extends BaseMapper<SysDict> {

    /** 全部字典类型（含系统内置，忽略租户过滤）。 */
    @org.apache.ibatis.annotations.Select(
            "select distinct dict_type from bp_sys_dict"
            + " where dict_status = 'ENABLED' order by dict_type")
    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<String> distinctTypes();

    /** 按类型取字典项（含系统内置，忽略租户过滤）。 */
    @org.apache.ibatis.annotations.Select(
            "select * from bp_sys_dict where dict_type = #{dictType}"
            + " and dict_status = 'ENABLED' order by sort_no asc, id asc")
    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<SysDict> selectByTypeIgnoreTenant(@org.apache.ibatis.annotations.Param("dictType")
                                                     String dictType);

    /** 按类型取全部字典项（含已停用，管理页用）。 */
    @org.apache.ibatis.annotations.Select(
            "select * from bp_sys_dict where dict_type = #{dictType}"
            + " order by sort_no asc, id asc")
    @com.baomidou.mybatisplus.annotation.InterceptorIgnore(tenantLine = "true")
    java.util.List<SysDict> selectByTypeAll(@org.apache.ibatis.annotations.Param("dictType")
                                            String dictType);
}
