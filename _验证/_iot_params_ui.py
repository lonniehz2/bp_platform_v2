# -*- coding: utf-8 -*-
"""系统参数页：新增「IoT 对接参数」分组编辑区。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 1) api 增加 setConfig
P = os.path.join(ROOT, 'frontend', 'src', 'api', 'modules.js')
s = io.open(P, encoding='utf-8').read()
if 'setConfig:' not in s:
    s = s.replace("  configs: (group) => req.get('/sys/configs', { params: { group } }),",
"""  configs: (group) => req.get('/sys/configs', { params: { group } }),
  setConfig: (data) => req.post('/sys/configs', data),""", 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('sysApi.setConfig 已加')

# 2) SysAdmin.vue：参数区加 IoT 卡片
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'SysAdmin.vue')
s = io.open(P, encoding='utf-8').read()

CARD = """
        <!-- IoT 对接参数（契约参数，可配置） -->
        <el-card shadow="never" style="margin-bottom:14px"
                 body-style="padding:12px 14px">
          <div class="toolbar" style="margin-bottom:10px">
            <h4 style="margin:0">IoT 对接参数</h4>
            <el-tag size="small" type="info">分组 IOT · 与 IoT 平台联调前先确认</el-tag>
            <div class="spacer" />
            <el-button size="small" @click="loadIotConfigs">重新读取</el-button>
            <el-button size="small" type="primary" :loading="iotSaving"
                       @click="saveIotAll">保存全部</el-button>
          </div>
          <el-table :data="iotRows" border size="small">
            <el-table-column prop="label" label="参数" width="230" />
            <el-table-column label="值" width="260">
              <template #default="{ row }">
                <el-select v-if="row.options" v-model="row.value" size="small"
                           style="width:100%">
                  <el-option v-for="o in row.options" :key="o.value"
                             :label="o.label" :value="o.value" />
                </el-select>
                <el-input v-else v-model="row.value" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="90" />
            <el-table-column prop="description" label="说明" min-width="260" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button link type="primary" @click="saveIotOne(row)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="muted" style="margin-top:8px">
            默认值：签名 v2-hmac-sha256、时间容忍 300 秒、指令超时 10 秒 / 重试 3 次、
            授权任务超时 180 秒、心跳 60 秒 / 离线 180 秒、表计上报 每日。
            修改后立即生效，无需重启。
          </div>
        </el-card>
"""

if 'IoT 对接参数' not in s:
    s = s.replace("""      <el-tab-pane label="系统参数" name="config">
        <div class="toolbar" style="margin-bottom:8px">""",
"""      <el-tab-pane label="系统参数" name="config">""" + CARD + """
        <div class="toolbar" style="margin-bottom:8px">""", 1)

SCRIPT = """
// ---------------- IoT 对接参数（分组 IOT，可配置） ----------------
const IOT_META = [
  { key: 'iot.callback.signAlgorithm', label: '回调签名算法', unit: '',
    options: [{ label: 'v2-hmac-sha256（推荐）', value: 'v2-hmac-sha256' },
      { label: 'legacy-md5-aes（旧协议）', value: 'legacy-md5-aes' }],
    description: '回调验签使用的算法' },
  { key: 'iot.callback.timestampToleranceSeconds', label: '时间戳容忍窗口', unit: '秒',
    description: '超出该窗口的回调视为重放，直接拒绝' },
  { key: 'iot.callback.nonceCacheMinutes', label: 'Nonce 缓存时长', unit: '分钟',
    description: '防重放窗口内相同 Nonce 只接受一次' },
  { key: 'iot.callback.batchLimit', label: '单次批量上限', unit: '条',
    description: '回调/批量接口单次最大条数' },
  { key: 'iot.callback.qps', label: '回调限流', unit: '次/秒',
    description: '0 表示不限流' },
  { key: 'iot.command.timeoutSeconds', label: '指令超时', unit: '秒',
    description: '超时转 TIMEOUT 并按重试次数重发' },
  { key: 'iot.command.maxRetry', label: '指令最大重试', unit: '次',
    description: '超过后置 FAILED 并告警' },
  { key: 'iot.grantTask.timeoutSeconds', label: '授权任务超时', unit: '秒',
    description: '授权下发未回执的超时判定' },
  { key: 'iot.heartbeat.intervalSeconds', label: '心跳间隔', unit: '秒',
    description: 'IoT 上报心跳的参考频率（告知 IoT 方）' },
  { key: 'iot.offline.thresholdSeconds', label: '离线判定阈值', unit: '秒',
    description: '超过该时长无心跳即判离线并产生事件' },
  { key: 'iot.meter.reportPeriod', label: '表计上报周期', unit: '',
    description: '如 ELEC:DAILY,WATER:DAILY（电表/水表均为每日）' },
  { key: 'iot.meter.switch.delayMinutes', label: '拉闸延迟', unit: '分钟',
    description: '延迟执行窗口内可撤销' }
]

const iotRows = ref(IOT_META.map((m) => ({ ...m, value: '' })))
const iotSaving = ref(false)

async function loadIotConfigs() {
  try {
    const list = await sysApi.configs('IOT') || []
    const map = {}
    list.forEach((x) => { map[x.configKey] = x.configValue })
    iotRows.value = IOT_META.map((m) => ({ ...m, value: map[m.key] ?? '' }))
  } catch (e) {
    iotRows.value = IOT_META.map((m) => ({ ...m, value: '' }))
  }
}

async function saveIotOne(row) {
  if (row.value === '' || row.value === null || row.value === undefined) {
    ElMessage.warning('『' + row.label + '』不能为空')
    return
  }
  await sysApi.setConfig({ key: row.key, value: String(row.value), description: row.description })
  ElMessage.success('已保存：' + row.label)
}

async function saveIotAll() {
  iotSaving.value = true
  try {
    for (const row of iotRows.value) {
      if (row.value === '' || row.value === null || row.value === undefined) continue
      await sysApi.setConfig({ key: row.key, value: String(row.value), description: row.description })
    }
    ElMessage.success('IoT 对接参数已全部保存')
    loadIotConfigs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally { iotSaving.value = false }
}
"""

if 'loadIotConfigs' not in s:
    s = s.replace('</script>', SCRIPT + '</script>', 1)

# 引入 ElMessage（若未引入）与 onMounted 调用
if 'ElMessage' not in s.split('<script setup>')[1][:800]:
    s = s.replace("import { sysApi } from '@/api/modules'",
                  "import { sysApi } from '@/api/modules'\nimport { ElMessage } from 'element-plus'", 1)

if 'loadIotConfigs()' not in s.split('onMounted')[1][:400] if 'onMounted' in s else True:
    s = s.replace('onMounted(() => {', 'onMounted(() => {\n  loadIotConfigs()', 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('SysAdmin.vue 已加 IoT 参数卡片')
