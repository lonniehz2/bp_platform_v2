# 房源权限面板与外部能力接口定义

## 1. 房源权限面板

### 1.1 查询房源权限

```http
GET /api/v1/house-access/{houseId}
```

返回：

```json
{
  "house": {
    "id": 1,
    "houseCode": "101",
    "houseName": "1-101",
    "spaceId": 1001,
    "houseStatus": "OCCUPIED",
    "orgId": 10
  },
  "contract": {
    "id": 20,
    "contractNo": "BC...",
    "personId": 30,
    "lesseeName": "张三",
    "contractStatus": "EFFECTIVE",
    "leaseStart": "2026-01-01",
    "leaseEnd": "2027-12-31"
  },
  "entitlements": [
    {
      "id": 40,
      "grantNo": "BG...",
      "grantLevel": "USAGE",
      "personId": 30,
      "validStart": "2026-01-01T00:00:00",
      "validEnd": "2027-12-31T23:59:59",
      "grantStatus": "EFFECTIVE"
    }
  ],
  "keyrings": [],
  "deviceCount": 2
}
```

### 1.2 冻结开门权限

```http
POST /api/v1/house-access/{houseId}/freeze
Content-Type: application/json

{"reason": "欠费冻结"}
```

返回：

```json
{"revoked": 1}
```

### 1.3 恢复权限

```http
POST /api/v1/house-access/{houseId}/restore
```

按当前有效合同重新下发 `USAGE` 授权，有效期至合同止租日。

### 1.4 临时权限

```http
POST /api/v1/house-access/{houseId}/temporary
Content-Type: application/json

{
  "personId": 30,
  "grantLevel": "VISIT",
  "validStart": "2026-11-04T10:00:00",
  "validEnd": "2026-11-05T18:00:00"
}
```

### 1.5 应急密码

```http
POST /api/v1/house-access/{houseId}/emergency-password
Content-Type: application/json

{"personId": 30, "hours": 24}
```

返回：

```json
{"keyringId": 50, "code": "123456", "expireTime": "2026-11-05T10:00:00"}
```

当前实现使用离线激活码介质，密码为系统生成的 6 位数字，有效期最长 168 小时。

---

## 2. 短信接口（待 IoT 平台提供）

权限面板、欠费、到期、违规处置需要统一短信发送能力。建议接口：

```http
POST /api/v1/iot/sms/send
Content-Type: application/json

{
  "tenantId": "350600",
  "mobile": "13800000000",
  "templateCode": "HOUSE_ACCESS_FROZEN",
  "templateParams": {
    "houseName": "1-101",
    "reason": "欠费冻结"
  },
  "bizType": "ACCESS",
  "bizId": "40"
}
```

返回：

```json
{
  "code": "BP00000",
  "data": {
    "messageId": "SMS...",
    "status": "SUBMITTED"
  }
}
```

需要 IoT 平台提供：

- 短信模板编码及变量规范
- 发送回执/状态查询接口
- 测试手机号白名单
- 限流和费用归属规则

建议回调：

```http
POST /api/v1/iot/sms/callback
Content-Type: application/json

{
  "messageId": "SMS...",
  "mobile": "13800000000",
  "status": "DELIVERED",
  "errorCode": null,
  "deliveredAt": "2026-11-04T12:00:00"
}
```

---

## 3. 身份证读卡器接口（待 IoT 平台提供）

浏览器无法直接访问串口/USB 读卡器，需要本地服务或浏览器插件桥接。

### 3.1 推荐方式：本地 HTTP 服务

```http
POST http://127.0.0.1:18666/idcard/read
```

返回：

```json
{
  "success": true,
  "name": "张三",
  "idCard": "350600199001011234",
  "gender": "M",
  "nation": "汉",
  "birthday": "1990-01-01",
  "address": "...",
  "issuingAuthority": "...",
  "validStart": "2020-01-01",
  "validEnd": "2040-01-01",
  "photoBase64": "..."
}
```

失败：

```json
{"success": false, "code": "NO_CARD", "message": "未检测到身份证"}
```

### 3.2 浏览器桥接

如果 IoT 平台提供浏览器插件，可暴露：

```javascript
window.__ID_CARD_READER__ = {
  read: async () => ({
    name: '张三',
    idCard: '350600199001011234'
  })
}
```

统一查询页面已预留 `window.__ID_CARD_READER__`，赋值后点击“读取身份证”即可自动回填。

### 3.3 安全要求

- 身份证号、姓名、照片不得写入前端日志
- 本地服务仅监听 `127.0.0.1`
- 后端落库继续使用密文 + 哈希 + 脱敏三列
- 读卡结果不应长期保存在浏览器 localStorage

---

## 4. 语音播报接口

### 4.1 Windows 电脑直接播报

当前实现使用浏览器原生 `SpeechSynthesis`：

```javascript
const u = new SpeechSynthesisUtterance(text)
u.lang = 'zh-CN'
speechSynthesis.speak(u)
```

要求：

- 使用 Edge/Chrome
- Windows 已安装中文语音包
- 不需要额外第三方硬件

播报文字在房源权限面板中可编辑，默认模板：

```text
{house}，承租人{person}，房源权限操作已完成
```

### 4.2 第三方语音硬件

如果后续使用音柱、广播网关，建议接口：

```http
POST /api/v1/iot/voice/speak
Content-Type: application/json

{
  "deviceId": "VOICE-001",
  "text": "1-101 房源权限已冻结",
  "volume": 80,
  "repeat": 1
}
```

返回：

```json
{"taskId": "VOICE...", "status": "ACCEPTED"}
```

需要 IoT 平台提供：

- 语音设备发现/绑定接口
- 文本转语音服务地址
- 播报任务状态回调

当前阶段先使用 Windows 浏览器播报，不依赖第三方硬件。
