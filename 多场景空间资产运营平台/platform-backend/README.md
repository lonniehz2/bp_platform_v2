# platform-backend

> 新平台后端工程目录规划  
> 端口：8090（开发/UAT）  
> 数据库：`bp_platform_v2`

## 模块规划

```text
platform-core        租户/组织/场景/菜单/权限/公共
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

## 包名建议

```text
com.yundao.platform.core
com.yundao.platform.asset
com.yundao.platform.person
com.yundao.platform.workflow
com.yundao.platform.contract
com.yundao.platform.booking
com.yundao.platform.billing
com.yundao.platform.discount
com.yundao.platform.device
com.yundao.platform.grant
com.yundao.platform.scene.guarantee
com.yundao.platform.scene.property
```

## 原则

```text
平台模块不依赖 guarantee_*/prop_* 表
场景模块依赖平台接口
IOT/停车通过适配器接入
```

当前未生成 Java 代码，等待框架评审。
