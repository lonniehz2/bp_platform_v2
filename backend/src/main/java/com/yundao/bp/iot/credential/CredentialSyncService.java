package com.yundao.bp.iot.credential;

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
