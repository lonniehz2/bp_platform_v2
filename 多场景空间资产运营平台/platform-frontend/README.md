# platform-frontend

> 新平台前端工程目录规划  
> 开发端口：5174  
> 后端 API：8090

## 页面组织

```text
src/
├─ platform/          平台基础页面
│  ├─ tenant
│  ├─ scene
│  ├─ asset
│  ├─ person
│  ├─ workflow
│  ├─ device
│  └─ system
├─ scenes/
│  ├─ guarantee      保障房场景
│  ├─ property       物业场景
│  ├─ apartment      公寓
│  ├─ office         办公
│  ├─ hotel          酒店/民宿
│  └─ campus         校园
├─ layout/            场景化布局
├─ router/            动态路由
└─ store/             场景/项目上下文
```

## 菜单组合

```text
scene_profile
+ business_mode
+ feature_flag
+ role_template
```

不同场景输出不同菜单，不做巨型菜单。

## 原则

```text
老系统前端保留
新平台独立前端
生产通过子域名/网关切换
不把新代码写进老前端目录
```

当前未生成前端代码，等待框架评审。
