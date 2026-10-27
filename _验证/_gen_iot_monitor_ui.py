# -*- coding: utf-8 -*-
"""IoT 监控页面。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

VIEW = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">IoT 监控</h3>
      <el-tag size="small" type="info">设备在线 / 指令 / 回调</el-tag>
      <div class="spacer" />
      <el-select v-model="hours" style="width:130px" @change="load">
        <el-option label="近 24 小时" :value="24" />
        <el-option label="近 72 小时" :value="72" />
        <el-option label="近 7 天" :value="168" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">设备在线率</div>
          <div class="num">{{ m.devices?.onlineRate ?? 0 }}%</div>
          <div class="muted">在线 {{ m.devices?.online ?? 0 }} / 共 {{ m.devices?.total ?? 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">指令成功率</div>
          <div class="num">{{ m.commands?.successRate ?? 0 }}%</div>
          <div class="muted">成功 {{ m.commands?.success ?? 0 }} / 共 {{ m.commands?.total ?? 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">回调成功率</div>
          <div class="num">{{ m.callbacks?.successRate ?? 0 }}%</div>
          <div class="muted">已处理 {{ m.callbacks?.done ?? 0 }} / 共 {{ m.callbacks?.total ?? 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">Nonce 记录</div>
          <div class="num">{{ m.nonceCount ?? 0 }}</div>
          <div class="muted">防重放缓存条数</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">指令状态分布</div>
          <el-table :data="statusRows(m.commands?.byStatus)" border size="small">
            <el-table-column prop="name" label="状态" />
            <el-table-column prop="value" label="数量" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">回调动作分布</div>
          <el-table :data="statusRows(m.callbacks?.byAction)" border size="small">
            <el-table-column prop="name" label="动作" />
            <el-table-column prop="value" label="数量" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">事件 Top（{{ hours }}h）</div>
          <el-table :data="m.events?.top || []" border size="small">
            <el-table-column prop="identifier" label="类型" />
            <el-table-column prop="count" label="数量" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <div class="muted" style="margin-top:10px">
      统计窗口：{{ hours }} 小时 ｜ 生成时间：{{ m.generatedAt || '—' }}
    </div>
  </div>
</template>

<script setup>
/**
 * IoT 监控：在线率、指令成功率、回调成功率、事件分布。
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const hours = ref(24)
const loading = ref(false)
const m = ref({})

function statusRows(map) {
  if (!map) return []
  return Object.keys(map).map((k) => ({ name: k, value: map[k] }))
}

async function load() {
  loading.value = true
  try {
    m.value = await req.get('/iot/metrics', { params: { hours: hours.value } })
  } catch (e) {
    ElMessage.error('监控指标加载失败')
  } finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.num { font-size: 26px; font-weight: 600; margin: 4px 0; }
.card-title { font-weight: 600; margin-bottom: 8px; }
</style>
'''

open(os.path.join(ROOT, 'frontend', 'src', 'views', 'IotMonitor.vue'), 'w',
     encoding='utf-8', newline='').write(VIEW)
print('IotMonitor.vue 已创建')

p = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')
s = io.open(p, encoding='utf-8').read()
if "'/iot-monitor'" not in s:
    s = s.replace("""  {
    path: '/iot-tools',""", """  {
    path: '/iot-monitor',
    name: 'IotMonitor',
    component: () => import('@/views/IotMonitor.vue'),
    meta: { title: 'IoT监控', icon: 'DataLine', group: '设备与通行',
      perm: 'asset:device:view' }
  },
  {
    path: '/iot-tools',""", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('路由已加 /iot-monitor')

p = os.path.join(ROOT, 'frontend', 'src', 'layout', 'menuConfig.js')
s = io.open(p, encoding='utf-8').read()
s = s.replace("paths: ['/devices', '/device-bind', '/dev-events', '/dev-commands', '/iot-tools']",
              "paths: ['/devices', '/device-bind', '/dev-events', '/dev-commands', '/iot-tools', '/iot-monitor']", 1)
s = s.replace("'/iot-tools': 64,", "'/iot-tools': 64, '/iot-monitor': 65,", 1)
s = s.replace("'/iot-tools': '验签自测、回调日志与重放',",
              "'/iot-tools': '验签自测、回调日志与重放',\n  '/iot-monitor': '在线率、指令与回调成功率',", 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('菜单已加 /iot-monitor')
