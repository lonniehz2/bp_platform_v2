package com.yundao.bp.sys.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

/**
 * 全国五级行政区划（省/市/区县/街道乡镇/社区村）。
 *
 * <p>数据来源：国家统计局行政区划代码；用于组织地址的级联选择。
 */
@TableName("bp_sys_region")
public class SysRegion {

    /** 行政区划代码（12 位） */
    @TableId
    private String code;

    private String name;

    private String parentCode;

    /** 1=省 2=市 3=区县 4=街道乡镇 5=社区村 */
    private Integer level;

    private Integer hasChild;

    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getParentCode() { return parentCode; }
    public void setParentCode(String parentCode) { this.parentCode = parentCode; }

    public Integer getLevel() { return level; }
    public void setLevel(Integer level) { this.level = level; }

    public Integer getHasChild() { return hasChild; }
    public void setHasChild(Integer hasChild) { this.hasChild = hasChild; }
}
