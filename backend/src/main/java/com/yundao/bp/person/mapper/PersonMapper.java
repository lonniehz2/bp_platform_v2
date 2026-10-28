package com.yundao.bp.person.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.person.entity.Person;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PersonMapper extends BaseMapper<Person> {

    /** 显示用：包含已逻辑删除的人员，保证历史单据里的人名不丢。 */
    @org.apache.ibatis.annotations.Select(
            "select person_name from bp_person where id = #{id} limit 1")
    String selectNameIncludeDeleted(
            @org.apache.ibatis.annotations.Param("id") Long id);
}
