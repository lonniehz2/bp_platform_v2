# -*- coding: utf-8 -*-
"""标注可豁免的数据范围项，并给剩余业务列表补齐范围。

豁免类别：
  * 配置/公共数据（计费项、补贴标准、消息模板、开放平台、报表模板）
  * 按父对象限权但参数名未被识别（listByPerson / listByHandleStatus / listByHouseAndDate）
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BP = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# (相对路径, 方法名) → 豁免原因
IGNORES = [
    ('asset/service/impl/HouseCalendarServiceImpl.java', 'searchAvailable', '可售房源属公开查询'),
    ('biz/service/impl/CreditServiceImpl.java', 'listByPerson', '按人员参数限权'),
    ('biz/service/impl/ShortRentOrderServiceImpl.java', 'listByHouseAndDate', '按房源+日期限权'),
    ('fin/service/impl/FeeItemServiceImpl.java', 'pageFeeItems', '计费项为租户级配置'),
    ('fin/service/impl/SubsidyServiceImpl.java', 'pageStandards', '补贴标准为租户级配置'),
    ('grant/service/impl/GrantReconcileServiceImpl.java', 'listByHandleStatus', '对账差异按状态查询'),
    ('grant/service/impl/KeyringServiceImpl.java', 'listByPerson', '按人员参数限权'),
    ('msg/service/impl/MessageServiceImpl.java', 'listTemplates', '消息模板为配置数据'),
    ('open/service/impl/OpenPlatformServiceImpl.java', 'listApps', '开放平台配置'),
    ('open/service/impl/OpenPlatformServiceImpl.java', 'listApis', '开放平台配置'),
    ('open/service/impl/OpenPlatformServiceImpl.java', 'pageCallLogs', '开放平台调用日志'),
    ('rpt/service/impl/ReportServiceImpl.java', 'listReports', '报表模板配置'),
    ('biz/service/impl/AllocationServiceImpl.java', 'pageBatch', '批次为组织级作业对象'),
]

# 需要补范围的业务列表：(路径, 方法, 实体, org 列, person 列)
PATCH = [
    ('ops/service/impl/InspectionPlanServiceImpl.java', 'page',
     'OpsInspectionPlan', 'OpsInspectionPlan::getOrgId', None),
    ('ops/service/impl/VisitServiceImpl.java', 'page',
     'OpsHouseVisit', 'OpsHouseVisit::getOrgId', 'OpsHouseVisit::getPersonId'),
    ('grant/service/impl/GrantServiceImpl.java', 'page',
     'GrantEntitlement', 'GrantEntitlement::getOrgId', 'GrantEntitlement::getPersonId'),
]


def add_ignore(rel, method, reason):
    path = os.path.join(BP, rel.replace('/', os.sep))
    if not os.path.exists(path):
        print('缺文件:', rel)
        return
    s = io.open(path, encoding='utf-8', errors='replace').read()
    if '// scope:ignore ' + reason in s:
        return
    m = re.search(r'public\s+\S+<\S+>\s+' + method + r'\s*\(', s)
    if not m:
        print('未找到方法:', rel, method)
        return
    brace = s.find('{', m.end())
    if brace < 0:
        return
    s = s[:brace + 1] + '\n        // scope:ignore ' + reason + s[brace + 1:]
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('已标注豁免:', os.path.basename(rel), method)


for rel, method, reason in IGNORES:
    add_ignore(rel, method, reason)
