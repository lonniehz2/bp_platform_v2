# -*- coding: utf-8 -*-
"""更新忽略清单守卫测试：纳入 3 张新增全局定义表并说明理由"""
import io

p = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\iam\IamModuleTest.java'
s = io.open(p, encoding='utf-8').read()

old = '''        Set<String> ignore = MybatisTenantConfig.IGNORE_TABLES;
        // 只允许这些全局表；新增会在此失败，从而触发评审
        assertEquals(Set.of("bp_iam_tenant", "bp_iam_permission", "bp_sys_dict",
                "bp_msg_template", "bp_open_api"), ignore);'''

new = '''        Set<String> ignore = MybatisTenantConfig.IGNORE_TABLES;
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
        //   bp_open_api           开放接口清单
        assertEquals(Set.of("bp_iam_tenant", "bp_iam_permission", "bp_sys_dict",
                "bp_sys_config", "bp_msg_template", "bp_rpt_report_def",
                "bp_rpt_screen_def", "bp_open_api"), ignore);'''

assert old in s, '锚点缺失'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 忽略清单守卫测试已更新（含 3 张新增全局定义表 + 理由）')
