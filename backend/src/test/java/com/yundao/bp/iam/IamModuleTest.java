package com.yundao.bp.iam;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.config.MybatisTenantConfig;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.iam.dto.OrgCreateCmd;
import com.yundao.bp.iam.dto.OrgVO;
import com.yundao.bp.iam.entity.IamOrg;
import com.yundao.bp.iam.mapper.IamOrgMapper;
import com.yundao.bp.iam.service.OrgService;
import com.yundao.bp.iam.service.impl.OrgServiceImpl;
import java.util.Set;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/**
 * iam 模块测试：
 * <ol>
 *   <li><b>租户插件忽略清单守卫</b>——防止误加忽略表导致越权</li>
 *   <li>组织服务业务规则（编码唯一、父子层级、删除保护）</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
class IamModuleTest {

    @Mock
    private IamOrgMapper orgMapper;

    private OrgService orgService;

    @BeforeEach
    void setUp() {
        orgService = new OrgServiceImpl(orgMapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    // ==================== 忽略清单守卫 ====================

    @Test
    @DisplayName("租户插件忽略清单必须最小化（仅全局表）")
    void ignoreTablesMinimal() {
        Set<String> ignore = MybatisTenantConfig.IGNORE_TABLES;
        // 只允许这些「全局定义 + 租户可覆盖」的表；新增会在此失败，从而触发评审。
        //
        // 忽略理由（必须逐条可解释，否则就是绕过租户隔离）：
        //   bp_iam_tenant         租户主表本身，无 tenant_id 列
        //   bp_iam_permission     全局权限资源定义
        //   bp_sys_dict           系统内置字典（NULL=内置，租户可覆盖）
        //   bp_sys_config         系统参数（全局默认 + 租户覆盖，由 ConfigService 合并）
        //   bp_msg_template       系统内置消息模板（租户可覆盖）
        //   bp_rpt_report_def     报表定义（全局默认 + 租户覆盖）
        //   bp_rpt_screen_def     大屏定义（全局默认 + 租户覆盖）
        //   bp_open_call_log      开放平台调用日志，按 appKey 归属，表无 tenant_id 列
        //                         （不忽略会导致租户插件给 INSERT 注入 tenant_id 而写入失败）
        //   bp_open_api           开放接口清单
        assertEquals(Set.of("bp_iam_tenant", "bp_iam_permission", "bp_sys_dict",
                "bp_sys_config", "bp_msg_template", "bp_rpt_report_def",
                "bp_rpt_screen_def", "bp_open_api", "bp_open_call_log"),
                MybatisTenantConfig.IGNORE_TABLES);
        OrgVO vo = orgService.create(new OrgCreateCmd(
                "ZZ0001", "第1期小区", null, "COMMUNITY",
                null, null, null, null, null,
                "福建省漳州市", 1, null, null, null, null, null, null));

        assertEquals("ZZ0001", vo.orgCode());
        assertEquals(1, vo.orgLevel());
        assertEquals("", vo.orgPath());
        assertEquals("ENABLED", vo.status());
        assertTrue(vo.id() > 0);
    }

    @Test
    @DisplayName("创建子组织：level 递增，path 追加父ID")
    void createChildOrg() {
        IamOrg parent = new IamOrg();
        parent.setId(900001L);
        parent.setOrgLevel(1);
        parent.setOrgPath("");

        when(orgMapper.selectCount(any())).thenReturn(0L);
        when(orgMapper.selectById(900001L)).thenReturn(parent);
        when(orgMapper.insert(any(IamOrg.class))).thenReturn(1);

        OrgVO vo = orgService.create(new OrgCreateCmd(
                "ZZ0001-01", "1幢", 900001L, "COMMUNITY",
                null, null, null, null, null, null, 1, null, null, null, null, null, null));

        assertEquals(2, vo.orgLevel());
        assertEquals("900001/", vo.orgPath());
    }

    @Test
    @DisplayName("组织编码重复应拒绝")
    void duplicateOrgCodeRejected() {
        when(orgMapper.selectCount(any())).thenReturn(1L);

        BizException ex = assertThrows(BizException.class, () ->
                orgService.create(new OrgCreateCmd(
                        "ZZ0001", "重复", null, "COMMUNITY",
                null, null, null, null, null, null, 1, null, null, null, null, null, null)));
        assertEquals(ErrorCode.DUPLICATED, ex.errorCode());
    }

    @Test
    @DisplayName("父组织不存在应拒绝")
    void parentNotFoundRejected() {
        when(orgMapper.selectCount(any())).thenReturn(0L);
        when(orgMapper.selectById(888888L)).thenReturn(null);

        BizException ex = assertThrows(BizException.class, () ->
                orgService.create(new OrgCreateCmd(
                        "X", "X", 888888L, "COMMUNITY", null, null, null, null, null, null, 1, null, null, null, null, null, null)));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("存在下级组织时不允许删除")
    void deleteWithChildrenRejected() {
        when(orgMapper.selectCount(any())).thenReturn(2L);

        BizException ex = assertThrows(BizException.class, () -> orgService.delete(900001L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("查询不存在的组织抛 NOT_FOUND")
    void getNotFound() {
        when(orgMapper.selectById(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> orgService.get(1L));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("无租户上下文时任何写操作都应被拒绝（安全底线）")
    void noTenantContextRejected() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, () ->
                orgService.create(new OrgCreateCmd(
                        "A", "A", null, "COMMUNITY", null, null, null, null, null, null, 1, null, null, null, null, null, null)));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }
}
