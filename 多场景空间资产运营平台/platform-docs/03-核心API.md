# 平台核心 API（Phase 0）

> Base URL：`http://127.0.0.1:8090`  
> 前缀：`/api/v1/platform`  
> 租户头：`X-Tenant-Id: 350600`

---

## 1. 场景

### GET /scenes

返回场景包及租户启用状态。

### GET /scenes/{sceneCode}/business-modes

返回场景下的经营模式。

---

## 2. 空间模板

### GET /space-templates?sceneCode=GUARANTEE

返回模板，`levels` 已解析为数组。

### POST /space-templates

```json
{
  "sceneCode": "GUARANTEE",
  "templateCode": "GUARANTEE_BASE",
  "templateName": "保障房基础",
  "baseLevelCount": 5,
  "allowedSubModes": "NONE,BED,INNER_ROOM,INNER_ROOM_BED",
  "levels": [
    {"level": 1, "name": "小区", "required": true},
    {"level": 2, "name": "楼栋", "required": true},
    {"level": 3, "name": "单元", "required": false},
    {"level": 4, "name": "楼层", "required": true},
    {"level": 5, "name": "房屋", "required": true}
  ]
}
```

校验：

```text
基础层级 2-6
层级数不少于基础层级
场景存在
模板编码唯一
```

---

## 3. 资产类型

### GET /asset-types?sceneCode=GUARANTEE

### POST /asset-types

```json
{
  "sceneCode": "GUARANTEE",
  "typeCode": "PUBLIC_RENTAL",
  "typeName": "公租房",
  "typeCategory": "HOUSE",
  "sortNo": 1
}
```

---

## 4. 项目

### GET /projects

### POST /projects

```json
{
  "orgCode": "GUA_DEMO",
  "orgName": "保障房示范项目",
  "sceneCode": "GUARANTEE",
  "businessMode": "PUBLIC_RENTAL",
  "spaceTemplateId": 910000000000003001,
  "defaultAssetTypeCode": "PUBLIC_RENTAL"
}
```

校验：

```text
租户启用场景
经营模式属于场景
模板属于场景且可用
项目编码唯一
```

---

## 5. 空间

### GET /projects/{projectId}/spaces

### POST /projects/{projectId}/spaces

```json
{
  "parentId": null,
  "spaceCode": "XQ",
  "spaceName": "示范小区",
  "spaceType": "AREA",
  "assetTypeCode": "PUBLIC_RENTAL",
  "rentable": false,
  "area": 0
}
```

空间类型：

```text
AREA
BUILDING
UNIT
FLOOR
ROOM
INNER_ROOM
BED
SITE
PARKING
```

规则：

```text
层级从 1 开始
基础层级内可创建
超出基础层级只能是 INNER_ROOM/BED
出租单元 rentable=true
```

---

## 6. 房源

### GET /projects/{projectId}/houses

空间创建时：

```text
spaceType = ROOM/INNER_ROOM/BED
rentable = true
```

自动生成 `bp_house`。

---

## 7. 验证脚本

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-core.ps1
```

预期：

```text
13 个断言通过
保障房 7 级空间树
3 个房源
```
