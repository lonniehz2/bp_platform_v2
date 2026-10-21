# -*- coding: utf-8 -*-
"""修正空间页：用 /spaces/tree（后端无分页列表接口）"""
import io
import json
import urllib.error
import urllib.request

P = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'

SRC = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">空间层级</h3>
      <el-tag size="small" type="info">
        小区 → 楼栋 → 单元 → 楼层 → 房 → 床
      </el-tag>
      <div class="spacer" />
      <el-input v-model.number="orgId" placeholder="组织ID（可空）"
                style="width:170px" @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button @click="expandAll = !expandAll">{{ expandAll ? '收起' : '展开' }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="后端只提供树形接口（/spaces/tree），无分页列表；path_code 每级 2 位"
              style="margin-bottom:12px" />

    <el-row :gutter="14">
      <el-col :span="9">
        <el-tree ref="treeRef" :data="tree" :props="{ label: 'spaceName', children: 'children' }"
                 node-key="id" :default-expand-all="expandAll" highlight-current
                 @node-click="onSelect">
          <template #default="{ data }">
            <span>
              {{ data.spaceName }}
              <el-tag size="small" type="info" style="margin-left:6px">
                {{ data.spaceType }}
              </el-tag>
            </span>
          </template>
        </el-tree>
        <el-empty v-if="!tree.length" description="暂无空间数据" :image-size="60" />
      </el-col>
      <el-col :span="15">
        <el-descriptions v-if="current" :column="2" border size="small"
                         title="空间详情">
          <el-descriptions-item label="ID">{{ current.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ current.spaceName }}</el-descriptions-item>
          <el-descriptions-item label="编码">{{ current.spaceCode }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ current.spaceType }}</el-descriptions-item>
          <el-descriptions-item label="路径编码">{{ current.pathCode }}</el-descriptions-item>
          <el-descriptions-item label="层级">{{ current.spaceLevel }}</el-descriptions-item>
          <el-descriptions-item label="面积">{{ current.area || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ current.status }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="点击左侧节点查看详情" :image-size="60" />
        <pre v-if="current" class="raw">{{ JSON.stringify(current, null, 2) }}</pre>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { spaceApi } from '@/api/modules'

const tree = ref([])
const current = ref(null)
const orgId = ref(null)
const expandAll = ref(true)
const treeRef = ref(null)

async function load() {
  try {
    const d = await spaceApi.tree({ orgId: orgId.value || undefined })
    tree.value = Array.isArray(d) ? d : (d?.rows || [])
  } catch (e) { tree.value = [] }
}

function onSelect(data) { current.value = data }

onMounted(load)
</script>

<style scoped>
.raw { max-height: 260px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; margin-top: 12px;
  white-space: pre-wrap; }
</style>
'''

io.open(P, 'w', encoding='utf-8').write(SRC)
print('  ✓ Spaces.vue 改为树形（/spaces/tree）')

# 补回字典（verify.py data 清过）
BASE = 'http://192.168.31.11:8080'


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return json.loads(x.read().decode())
    except Exception as e:
        return {'code': type(e).__name__}


tok = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')
r = call('GET', '/api/v1/spaces/tree', None, tok)
d = r.get('data')
print('  /spaces/tree → %s，节点 %d'
      % (r.get('code'), len(d) if isinstance(d, list) else 0))
