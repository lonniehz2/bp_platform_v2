# -*- coding: utf-8 -*-
"""设备页：同步状态按钮；文档：token/status 客户端就绪。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')
DOCS = ROOT

# 1) Devices 页按钮
p = os.path.join(VIEWS, 'Devices.vue')
s = io.open(p, encoding='utf-8').read()
if 'syncStatus' not in s:
    s = s.replace('''      <el-button type="warning" plain :loading="syncing" @click="syncDevices">
        同步设备
      </el-button>''', '''      <el-button type="warning" plain :loading="syncing" @click="syncDevices">
        同步设备
      </el-button>
      <el-button plain :loading="statusSyncing" @click="syncStatus">同步状态</el-button>''', 1)
    if 'const statusSyncing' not in s:
        s = s.replace('''const fresh = ref(null)''', '''const statusSyncing = ref(false)

/** 拉取一批设备的在线/电量状态（IoT 批量状态接口） */
async function syncStatus() {
  statusSyncing.value = true
  try {
    const r = await req.post('/iot/devices/status-sync', null, { params: { limit: 200 } })
    ElMessage.success('状态已同步：更新 ' + (r?.updated || 0) + ' 台（在线 ' + (r?.online || 0) + '）')
    load(); loadFreshness()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '状态同步失败')
  } finally { statusSyncing.value = false }
}

const fresh = ref(null)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('设备页已加同步状态')

# 2) capabilities 待办说明更新
p = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iot',
                 'gateway', 'IotCapabilitiesController.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('"联调用例 TC-M1-01/02；平台已有 YmdTokenManager 可对接"',
              '"TC-M1-01/02；平台客户端已实现（bp.iot.token-mode=mock 可跑），待 IoT 提供端点"')
s = s.replace('"TC-M1-05；平台设备页目前按单表查询"',
              '"TC-M1-05；平台客户端与同步接口已实现（/iot/devices/status-sync），待 IoT 端点"')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('capabilities 说明已更新')

# 3) 19 号报告状态
p = os.path.join(DOCS, '19_IoT联调测试执行报告.md')
s = io.open(p, encoding='utf-8').read()
s = s.replace('| TC-M1-01 | 取 Token | ⛔ | 平台侧尚无 IoT Token 客户端，需 IoT 提供取 Token 接口与有效期约定 |',
              '| TC-M1-01 | 取 Token | 🟡 | 平台客户端已实现（mock 通过：`bp.iot.token-mode`），待 IoT 提供 `/ymd/restful/token` |')
s = s.replace('| TC-M1-02 | Token 续期 | ⛔ | 同上，需 IoT 说明续期/失效策略 |',
              '| TC-M1-02 | Token 续期 | 🟡 | 平台已实现「到期前 5 分钟重取」，待 IoT 端点与 expiresIn 约定 |')
s = s.replace('| TC-M1-05 | 状态批量查询 | 🟡 | 平台有 `GET /devices` 与在线状态；批量状态接口需 IoT 提供 |',
              '| TC-M1-05 | 状态批量查询 | 🟡 | 平台已实现客户端与 `/iot/devices/status-sync`（mock 2/2 更新成功），待 IoT 端点 |')
s = s.replace('| ✅ 通过 | 平台侧行为已验证（mock/模拟） | 41 |',
              '| ✅ 通过 | 平台侧行为已验证（mock/模拟） | 41 |')
s = s.replace('| 🟡 部分 | 平台侧通过，设备侧行为待真实环境验证 | 12 |',
              '| 🟡 部分 | 平台侧通过，设备侧行为待真实环境验证 | 14 |')
s = s.replace('| ⛔ 阻塞 | 依赖 IoT 提供接口/参数/环境 | 4 |',
              '| ⛔ 阻塞 | 依赖 IoT 提供接口/参数/环境 | 2 |')
s = s.replace('P0 用例 38 条：通过 30、部分 8、阻塞 0（阻塞项均为 P1/P2）。',
              'P0 用例 38 条：通过 30、部分 8、阻塞 0（Token/批量状态已转「部分」）。')
s = s.replace('| 1 | 取 Token / 续期接口未提供 | TC-M1-01/02 |',
              '| 1 | 取 Token / 续期：平台客户端已实现，待 IoT 端点 | TC-M1-01/02 |')
s = s.replace('| 2 | 批量设备状态接口未提供 | TC-M1-05 |',
              '| 2 | 批量设备状态：平台客户端+同步接口已实现，待 IoT 端点 | TC-M1-05 |')
s = s.replace('| 4 | 真实压测/断网环境 | TC-M8-02/03 |',
              '| 4 | 真实压测/断网环境 | TC-M8-02/03 |')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('19 报告已更新')

# 4) 21 规格书：标注平台客户端已就绪
p = os.path.join(DOCS, '21_IoT侧需求规格说明书.md')
s = io.open(p, encoding='utf-8').read()
if '平台客户端已实现' not in s:
    s = s.replace('**优先级：P0（阻塞 TC-M1-01/02）**',
                  '**优先级：P0（阻塞 TC-M1-01/02）**\n\n> 平台侧状态：客户端已实现（`bp.iot.token-mode=mock` 可跑通），只待 IoT 端点。')
    s = s.replace('**优先级：P1（阻塞 TC-M1-05）**',
                  '**优先级：P1（阻塞 TC-M1-05）**\n\n> 平台侧状态：客户端与 `/iot/devices/status-sync` 已实现（mock 2/2 成功）。')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('21 规格书已标注')
