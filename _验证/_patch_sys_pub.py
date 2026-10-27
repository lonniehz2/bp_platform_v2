# -*- coding: utf-8 -*-
"""系统参数可编辑 + 公示中签标签修正。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------------- SysAdmin：系统参数修改 ----------------
p = os.path.join(VIEWS, 'SysAdmin.vue')
s = io.open(p, encoding='utf-8').read()

if 'configEditVisible' not in s:
    s = s.replace('''          <el-table-column prop="description" label="说明" min-width="240" />
        </el-table>''', '''          <el-table-column prop="description" label="说明" min-width="240" />
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" data-testid="sys-config-edit"
                         @click="openConfigEdit(row)">修改</el-button>
            </template>
          </el-table-column>
        </el-table>''', 1)

    # 弹窗
    s = s.replace('''    </el-tabs>''', '''    </el-tabs>

    <!-- 修改系统参数 -->
    <el-dialog v-model="configEditVisible" title="修改系统参数" width="560px">
      <el-form :model="configForm" label-width="90px">
        <el-form-item label="参数键">
          <el-input v-model="configForm.configKey" disabled />
        </el-form-item>
        <el-form-item label="当前值">
          <el-input v-model="configForm.oldValue" disabled />
        </el-form-item>
        <el-form-item label="新值" required>
          <el-input v-model="configForm.value" data-testid="sys-config-value"
                    placeholder="如 7" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="configForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" show-icon
                title="修改后立即生效；公示天数这类政策参数会影响后续业务校验，请谨慎调整。" />
      <template #footer>
        <el-button @click="configEditVisible = false">取消</el-button>
        <el-button type="primary" :loading="configSaving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>''', 1)

    # 状态与函数
    s = s.replace('''const configs = ref([])''', '''const configs = ref([])
const configEditVisible = ref(false)
const configSaving = ref(false)
const configForm = reactive({ configKey: '', oldValue: '', value: '', description: '' })

function openConfigEdit(row) {
  configForm.configKey = row.configKey
  configForm.oldValue = row.configValue
  configForm.value = row.configValue
  configForm.description = row.description || ''
  configEditVisible.value = true
}

async function saveConfig() {
  if (!configForm.value) { ElMessage.warning('请填写新值'); return }
  configSaving.value = true
  try {
    await sysApi.setConfig({
      key: configForm.configKey,
      value: String(configForm.value),
      description: configForm.description || undefined
    })
    ElMessage.success('已保存，新值立即生效')
    configEditVisible.value = false
    loadConfigs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally { configSaving.value = false }
}''', 1)

    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('SysAdmin 已加参数修改')
else:
    print('SysAdmin 已存在修改功能')

# ---------------- Publicities：中签标签 ----------------
p2 = os.path.join(VIEWS, 'Publicities.vue')
t = io.open(p2, encoding='utf-8').read()
if "=== 'WIN'" in t:
    t = t.replace("=== 'WIN'", "=== 'WON'")
    io.open(p2, 'w', encoding='utf-8', newline='').write(t)
    print('Publicities 标签已修正')
else:
    print('Publicities 标签无需修改')
