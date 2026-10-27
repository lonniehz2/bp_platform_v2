# -*- coding: utf-8 -*-
"""凭据（密码/卡/人脸/离线码）同步到 IoT：表、客户端、服务、钩子、接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def write(rel, body):
    path = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print('跳过(已存在)', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(body)
    print('创建', rel)


write('iot/credential/entity/IotCredentialSync.java', '''package com.yundao.bp.iot.credential.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 凭据同步记录。对应 {@code bp_iot_credential_sync}。 */
@Data
@TableName("bp_iot_credential_sync")
public class IotCredentialSync {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private Long keyringId;
    private Long personId;
    private String keyType;
    /** ADD / UPDATE / FREEZE / UNFREEZE / REMOVE */
    private String action;
    /** PENDING / SUCCESS / FAILED / SKIPPED */
    private String status;
    private String requestId;
    private String errorMsg;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
''')

write('iot/credential/mapper/IotCredentialSyncMapper.java', '''package com.yundao.bp.iot.credential.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iot.credential.entity.IotCredentialSync;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface IotCredentialSyncMapper extends BaseMapper<IotCredentialSync> {
}
''')

write('iot/credential/CredentialSyncClient.java', '''package com.yundao.bp.iot.credential;

/**
 * 凭据下发到 IoT（密码/卡/人脸/离线码）。
 *
 * <p>配置 {@code bp.credential.mode=mock|real}；real 实现待 IoT 参数确认。
 */
public interface CredentialSyncClient {

    Result sync(SyncRequest req);

    record SyncRequest(String requestId, Long personId, String keyType, String channelType,
                       String channelValue, String action) {
    }

    record Result(boolean success, String code, String message) {
    }
}
''')

write('iot/credential/MockCredentialSyncClient.java', '''package com.yundao.bp.iot.credential;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟凭据同步。 */
@Component
@ConditionalOnProperty(name = "bp.credential.mode", havingValue = "mock", matchIfMissing = true)
public class MockCredentialSyncClient implements CredentialSyncClient {

    private static final Logger log = LoggerFactory.getLogger(MockCredentialSyncClient.class);

    @Override
    public Result sync(SyncRequest req) {
        log.info("[mock] 凭据同步 {} person={} type={} action={}", req.requestId(),
                req.personId(), req.keyType(), req.action());
        return new Result(true, "0", "mock ok");
    }
}
''')

write('iot/credential/CredentialSyncService.java', '''package com.yundao.bp.iot.credential;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iot.credential.entity.IotCredentialSync;
import com.yundao.bp.iot.credential.mapper.IotCredentialSyncMapper;
import java.time.LocalDateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/** 凭据同步编排：记录请求、调用 IoT 客户端、回写结果。 */
@Service
public class CredentialSyncService {

    private static final Logger log = LoggerFactory.getLogger(CredentialSyncService.class);

    private final CredentialSyncClient client;
    private final IotCredentialSyncMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public CredentialSyncService(CredentialSyncClient client, IotCredentialSyncMapper mapper,
                                 SnowflakeIdGenerator idGen) {
        this.client = client;
        this.mapper = mapper;
        this.idGen = idGen;
    }

    /** 触发同步（失败不影响主流程）。 */
    public void sync(Long keyringId, Long personId, String keyType, String channelType,
                     String channelValue, String action) {
        try {
            long id = idGen.nextId();
            IotCredentialSync rec = new IotCredentialSync();
            rec.setId(id);
            rec.setTenantId(TenantContext.tenantId());
            rec.setKeyringId(keyringId);
            rec.setPersonId(personId);
            rec.setKeyType(keyType);
            rec.setAction(action);
            rec.setRequestId("CRD" + id);
            rec.setStatus("PENDING");
            rec.setCreateTime(LocalDateTime.now());
            rec.setUpdateTime(LocalDateTime.now());
            mapper.insert(rec);

            CredentialSyncClient.Result r = client.sync(
                    new CredentialSyncClient.SyncRequest(rec.getRequestId(), personId, keyType,
                            channelType, channelValue, action));
            rec.setStatus(r.success() ? "SUCCESS" : "FAILED");
            rec.setErrorMsg(r.success() ? null : r.message());
            rec.setUpdateTime(LocalDateTime.now());
            mapper.updateById(rec);
        } catch (Exception e) {
            log.warn("凭据同步失败 keyring={} action={}: {}", keyringId, action, e.getMessage());
        }
    }

    public PageResult<IotCredentialSync> page(long pageNum, long pageSize, Long keyringId,
                                              String status) {
        LambdaQueryWrapper<IotCredentialSync> qw = new LambdaQueryWrapper<IotCredentialSync>()
                .eq(keyringId != null, IotCredentialSync::getKeyringId, keyringId)
                .eq(status != null && !status.isBlank(), IotCredentialSync::getStatus, status)
                .orderByDesc(IotCredentialSync::getCreateTime);
        var p = mapper.selectPage(new com.baomidou.mybatisplus.extension.plugins.pagination.Page<>(
                pageNum, pageSize), qw);
        return PageResult.of(p.getTotal(), pageNum, pageSize, p.getRecords());
    }
}
''')

write('iot/credential/CredentialSyncController.java', '''package com.yundao.bp.iot.credential;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iot.credential.entity.IotCredentialSync;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 凭据同步记录查询（联调工具用）。 */
@RestController
@RequestMapping("/api/v1/iot")
public class CredentialSyncController {

    private final CredentialSyncService service;

    public CredentialSyncController(CredentialSyncService service) {
        this.service = service;
    }

    @RequirePerm("dev:command:view")
    @GetMapping("/credential-sync")
    public R<PageResult<IotCredentialSync>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long keyringId,
            @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, keyringId, status));
    }
}
''')

print('凭据同步模块文件已创建')
