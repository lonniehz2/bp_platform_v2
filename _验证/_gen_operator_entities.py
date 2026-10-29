# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\iam'

files = {}

files['entity/PlatformOperator.java'] = '''package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 平台运营超管（跨平台）。 */
@Data
@TableName("bp_iam_platform_operator")
public class PlatformOperator {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String username;
    private String passwordHash;
    private String realName;
    private String status;
    private Integer mustChangePassword;
    private Integer failCount;
    private LocalDateTime lockedUntil;
    private LocalDateTime lastLoginTime;
    private Integer isDeleted;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

files['entity/PlatformOperatorSession.java'] = '''package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 运营超管会话。 */
@Data
@TableName("bp_iam_platform_operator_session")
public class PlatformOperatorSession {
    @TableId(type = IdType.INPUT)
    private Long id;
    private Long operatorId;
    private String token;
    private String status;
    private LocalDateTime expireTime;
    private LocalDateTime createTime;
}
'''

files['entity/PlatformAudit.java'] = '''package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 平台运营审计。 */
@Data
@TableName("bp_iam_platform_audit")
public class PlatformAudit {
    @TableId(type = IdType.INPUT)
    private Long id;
    private Long operatorId;
    private String operatorName;
    private String platformCode;
    private String action;
    private String detail;
    private String ip;
    private LocalDateTime createTime;
}
'''

files['entity/TenantBranding.java'] = '''package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 平台品牌与主题。 */
@Data
@TableName("bp_iam_tenant_branding")
public class TenantBranding {
    @TableId(type = IdType.INPUT)
    private String tenantId;
    private String logoUrl;
    private String primaryColor;
    private String accentColor;
    private String loginTitle;
    private String loginSubtitle;
    private String menuStyle;
    private String colorMode;
    private Integer allowUserSwitch;
    private LocalDateTime updateTime;
}
'''

files['mapper/PlatformOperatorMapper.java'] = '''package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.PlatformOperator;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PlatformOperatorMapper extends BaseMapper<PlatformOperator> {
}
'''

files['mapper/PlatformOperatorSessionMapper.java'] = '''package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.PlatformOperatorSession;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PlatformOperatorSessionMapper extends BaseMapper<PlatformOperatorSession> {
}
'''

files['mapper/PlatformAuditMapper.java'] = '''package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.PlatformAudit;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PlatformAuditMapper extends BaseMapper<PlatformAudit> {
}
'''

files['mapper/TenantBrandingMapper.java'] = '''package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.TenantBranding;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TenantBrandingMapper extends BaseMapper<TenantBranding> {
}
'''

for rel, code in files.items():
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8', newline='').write(code)
    print('wrote', rel)
