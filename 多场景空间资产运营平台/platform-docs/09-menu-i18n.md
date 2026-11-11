# 09 菜单、多语言与多场景治理

## 左侧菜单

| 分组 | 说明 |
| --- | --- |
| 工作台 | 工作台、运营驾驶舱、统一查询、待办、审批、消息 |
| 租务管理 | 申请、人员、资格、轮候、配租、公示 |
| 合同管理 | 合同台账、变更、换房、退租 |
| 房源与资产 | 项目资产、空间、房源、日房态、展示、短租 |
| 收费与账务 | 账单、押金、补贴、资金、计费项、欠费 |
| 服务与监督 | 工单、投诉、申诉、回访 |
| 通行与设备 | 房源通行、设备、绑定、告警、记录、钥匙包、授权 |
| 风险与预警 | 预警、巡检、信用 |
| 数据与报表 | 报表中心、监管报送 |
| 系统管理 | 组织、用户权限、批量导入、系统支撑、帮助 |

菜单设计基线见 `platform-frontend/scripts/menu-design.json`。

## 场景

| 场景 | 标识 | 角色 |
| --- | --- | --- |
| 保障房 | GUARANTEE | GUARANTEE_ADMIN / MANAGER / FINANCE / STEWARD |
| 资产运营 | ASSET | ASSET_ADMIN / MANAGER / FINANCE / STEWARD |
| 服务运营 | SERVICE | SERVICE_ADMIN / MANAGER / FINANCE / STEWARD |

场景菜单、角色和用户绑定由 `platform-sql/025_scene_menus_roles.sql` 与
`platform-sql/026_scene_roles_cleanup.sql` 管理。

## 不可回退检查

前端 CI 执行：

```text
check-i18n --strict
check-i18n-en
check-scene
check-ui-labels
check-field-labels
check-menu-labels
check-report-csv
```

本地在服务启动后额外执行：

```text
check-scene-data
smoke-en-pages
```

## 规则

1. 页面与组件禁止硬编码中文和 `GUARANTEE`。
2. 枚举字段必须经过 `enumLabel` / `statusLabel` / 页面级翻译函数。
3. 新增详情字段必须在 i18n 的 `field.*` 中同时提供中英文。
4. 菜单名称以 `menu-design.json` 为基线，不允许前后端漂移。
5. 场景路由、菜单、角色、报表必须使用 `currentScene()` / `scenePath()`。
