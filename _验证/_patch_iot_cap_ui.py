# -*- coding: utf-8 -*-
"""IoT 联调工具：新增「对接能力」页签。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'IotTools.vue')
s = io.open(p, encoding='utf-8').read()

if '对接能力' not in s:
    s = s.replace('''      <el-tab-pane label="凭据同步" name="cred">''',
                  '''      <el-tab-pane label="对接能力" name="cap">
        <el-alert type="info" :closable="false" show-icon
                  title="展示当前接入模式、凭证配置与仍需 IoT 提供的能力（联调/上线切换前先看这里）"
                  style="margin-bottom:10px" />
        <el-row :gutter="12">
          <el-col :span="12">
            <div class="card-title">客户端模式</div>
            <el-table :data="capModeRows" size="small" border>
              <el-table-column prop="name" label="客户端" width="140" />
              <el-table-column prop="mode" label="当前模式" />
            </el-table>
            <div class="card-title" style="margin-top:12px">回调配置</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="验签">{{ cap.callback?.verify }}</el-descriptions-item>
              <el-descriptions-item label="回调 AppId">{{ cap.callback?.appId || '—' }}</el-descriptions-item>
              <el-descriptions-item label="时间戳窗口">
                {{ cap.callback?.timestampToleranceSeconds }} 秒
              </el-descriptions-item>
              <el-descriptions-item label="Nonce 缓存">
                {{ cap.callback?.nonceCacheMinutes }} 分钟
              </el-descriptions-item>
              <el-descriptions-item label="默认租户">{{ cap.callback?.defaultTenant }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
          <el-col :span="12">
            <div class="card-title">平台凭证</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="IoT 地址">{{ cap.iotCredential?.baseUrl || '—' }}</el-descriptions-item>
              <el-descriptions-item label="AppId">
                {{ cap.iotCredential?.appIdConfigured ? '已配置' : '未配置' }}
              </el-descriptions-item>
              <el-descriptions-item label="Secret">
                {{ cap.iotCredential?.appSecretConfigured ? '已配置' : '未配置' }}
              </el-descriptions-item>
              <el-descriptions-item label="可切真实环境">
                {{ cap.readyForReal ? '是' : '否（凭证未配齐）' }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="card-title" style="margin-top:12px">
              仍需 IoT 提供（{{ (cap.pendingFromIot || []).length }}）
            </div>
            <el-table :data="cap.pendingFromIot || []" size="small" border>
              <el-table-column prop="name" label="事项" min-width="180" show-overflow-tooltip />
              <el-table-column prop="note" label="说明" min-width="200" show-overflow-tooltip />
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="凭据同步" name="cred">''', 1)

    if 'const cap' not in s:
        s = s.replace('''const creds = ref([])''', '''const cap = ref({})
const capModeRows = computed(() => {
  const m = cap.value.modes || {}
  const name = { command: '指令下发', device: '设备台账', meter: '表计拉取', credential: '凭据下发' }
  return Object.keys(name).map((k) => ({ name: name[k], mode: m[k] || '—' }))
})

async function loadCapabilities() {
  try {
    cap.value = await req.get('/iot/capabilities')
  } catch (e) { cap.value = {} }
}

const creds = ref([])''', 1)
        # computed 是否已引入
        if 'computed' not in s.split('</script>')[0].split('import')[1] if False else False:
            pass
        if "import { ref, reactive, onMounted" in s and 'computed' not in s:
            s = s.replace("import { ref, reactive, onMounted", "import { ref, reactive, computed, onMounted", 1)
        s = s.replace("onMounted(() => { loadLogs(); loadCred() })",
                      "onMounted(() => { loadLogs(); loadCred(); loadCapabilities() })", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('对接能力页签已加')
