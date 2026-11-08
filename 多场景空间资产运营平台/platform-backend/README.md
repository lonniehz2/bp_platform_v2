# platform-backend

> 多场景平台后端  
> 端口：8090（开发/UAT）  
> 数据库：`bp_platform_v2`

## 当前已实现

```text
场景包查询
经营模式查询
空间结构模板查询/新增
资产类型查询/新增
项目创建/查询
空间节点创建/查询
房源自动创建/查询
人员创建/查询
人员与项目/空间/房屋关系
保障房合同
租金账单
收款/分摊/收据
审批/工作流
合同变更/退租
保障房申请/轮候/配租
配租转合同
押金收取/退还
退租释放房屋
补贴抵扣租金
设备业务资产
授权/人员钥匙包
菜单/角色模板
登录鉴权
资格复核
迁移异常处理
附件上传
菜单权限
租户上下文
统一返回和异常处理
```

接口前缀：

```text
/api/v1/platform
```

## 运行

初始化数据库：

```text
执行 platform-sql/001_platform_core.sql
数据库：bp_platform_v2
```

构建：

```powershell
$env:JAVA_HOME='D:\Work\tools\jdk-17.0.20.1+1'
D:\Work\tools\apache-maven-3.9.9\bin\mvn.cmd -B -q -DskipTests package -s D:\Work\tools\m2-settings.xml
```

启动：

```powershell
$env:DB_PASSWORD='******'
$env:SERVER_PORT='8090'
D:\Work\tools\jdk-17.0.20.1+1\bin\java.exe -jar target\multi-scene-platform.jar
```

## 自验证

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-core.ps1
```

验证结果：

```text
health
GUARANTEE 场景
PUBLIC_RENTAL 模式
创建模板
创建资产类型
创建项目
创建保障房 7 级空间树
创建房屋/内房/床位房源
创建人员
创建人员房屋关系
创建保障房合同
生成租金账单
收款
收据
审批流程
审批通过/驳回
合同变更审批
申请/轮候/配租
```

## 模块规划

```text
platform-core        租户/组织/场景/菜单/权限
platform-asset       空间模板/资产类型/空间/房屋
platform-person      人员主档/关系/标签/组
platform-workflow    审批/工作流
platform-contract    合同生命周期
platform-booking     预订/入住/库存日历
platform-billing     账单/收款/分摊/收据/发票
platform-discount    优惠/补贴
platform-device      设备业务资产
platform-grant       授权/人员钥匙包
platform-document    文档/PDF
platform-scenes
  guarantee-scene    保障房场景
  property-scene     物业场景
platform-web         对外 API
```

当前先用单模块工程快速验证核心链路，后续按模块拆分。
