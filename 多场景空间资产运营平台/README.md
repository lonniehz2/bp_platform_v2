# 多场景空间资产运营平台

> 目标：用一个平台承载保障房、物业、公寓、办公、酒店/民宿、网约房、宿舍、校园等场景  
> 当前阶段：Phase 0 平台框架设计  
> 第一场景：保障房  
> 第二场景：物业 V1

---

## 1. 项目定位

```text
平台基础能力
+ 平台业务能力
+ 场景包
+ 独立系统（IOT、智慧停车）
```

保障房不是平台，而是平台上的第一个场景包。

物业 V1 是第二个场景包。

---

## 2. 与老系统的关系

```text
老保障房系统：继续运行，冻结新增功能，仅做必要修复
新平台：独立目录、独立端口、独立数据库
迁移：老库只读，新库写入，按模块迁移
切换：保障房场景完成并验证后，域名/网关切到新平台
```

不直接修改老系统核心代码，不长期双写。

---

## 3. 运行环境约定

### 开发/UAT

```text
老系统：8080
新平台：8090
新前端：5174
新数据库：bp_platform_v2
```

### 生产

```text
https://guarantee.example.com
https://platform.example.com
```

生产不暴露裸端口，通过网关/子域名路由。

---

## 4. 目录结构

```text
多场景空间资产运营平台/
├─ platform-docs/           框架与场景设计
├─ platform-sql/            数据库草案与迁移脚本
├─ platform-backend/        平台后端
│  ├─ platform-core       租户/组织/场景/资产/人员
│  ├─ platform-workflow   审批/工作流
│  ├─ platform-contract   合同/预订/入住
│  ├─ platform-billing    账单/收款/发票
│  ├─ platform-device     设备业务资产
│  ├─ platform-grant      授权/钥匙包
│  ├─ platform-document   文档/PDF
│  └─ platform-scenes
│     ├─ guarantee        保障房场景
│     └─ property         物业场景
├─ platform-frontend/       平台前端
└─ README.md
```

---

## 5. 第一批设计文档

```text
platform-docs/00-平台框架设计.md
platform-docs/01-保障房场景映射.md
platform-docs/02-平台框架评审清单.md
platform-docs/03-核心API.md
platform-docs/04-实施进度.md
platform-docs/05-老数据迁移报告.md
platform-docs/06-前端操作台.md
platform-docs/07-保障房平台验收报告.md
platform-docs/08-部署说明.md
platform-docs/09-旧系统兼容说明.md
platform-docs/10-多语言与主题说明.md
platform-docs/11-浏览器回归报告.md
platform-docs/12-UI交互回归.md
platform-docs/13-新平台独立验收.md
platform-docs/14-菜单结构对照.md
platform-docs/15-驾驶舱与字段展示.md
platform-docs/16-字段校验与页面回归.md
platform-docs/17-方案A验收.md
platform-docs/18-设备绑定导入设计.md
platform-docs/19-多场景平台总体设计基线.md
platform-docs/20-保障房管理系统菜单结构设计.md
platform-docs/21-标准页面与页面模板阶段设计.md
platform-docs/22-房源产品化与线上展示设计.md
platform-docs/23-阶段0-范围与对象冻结.md
platform-docs/24-阶段1-页面模板与状态权限矩阵.md
platform-docs/25-阶段2-接口与选择器契约.md
platform-docs/26-阶段3-端到端业务纵切.md
platform-docs/27-阶段4-房源产品化详细设计.md
platform-docs/28-阶段5-五个参考页面详细设计.md
platform-docs/29-阶段6-原型走查与验收用例.md
platform-sql/001_platform_core.sql
platform-backend/README.md
platform-frontend/README.md
```

---

## 6. 当前优先级

```text
1. 平台框架设计
2. 保障房场景注册与基础适配
3. 物业 V1 第二个场景
4. 其他场景
```

---

## 7. 禁止事项

```text
不把老代码复制一份改名
不让平台表依赖 guarantee_*/prop_* 表
不长期双写
不在生产暴露裸端口
不把 IOT 控制、停车运营塞进业务平台
```


---

## 8. 已部署

```text
http://192.168.31.11:8090/
```

旧保障房系统仍在 8080，未覆盖。

## 9. 登录

```text
http://127.0.0.1:5174
租户 350600
admin / admin123
```

## 9. 当前已跑通

```text
平台服务 8090
数据库 bp_platform_v2
场景包 9 个
经营模式 17 个
保障房模板
保障房 7 级空间树
房屋/内房/床位房源
人员与房屋关系
保障房合同
租金账单
收款/收据
串行多级审批
合同变更审批
申请/轮候/配租/配租转合同
押金收取/退还
退租释放房屋
补贴抵扣租金
设备业务资产
授权/人员钥匙包
菜单/角色模板
```

前端：

```text
http://127.0.0.1:5174
```

自验证：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File platform-backend\scripts\verify-core.ps1
```

已验证 129 个断言通过。

前端页面：

```text
工作台
统一查询
使用帮助
项目与资产
客户与人员
申请与轮候
合同与租赁
收费与账务
设备与授权
菜单与角色
```


老数据迁移：

```text
组织 49
空间 172
房屋 151
人员 41
合同 27
账单 29/33
押金 13
补贴 4
补贴标准 3
合同变更 27
授权 10
设备 168
```

