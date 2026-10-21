# -*- coding: utf-8 -*-
"""角色配置页：把「基本信息 / 数据范围 / 权限」合并到一页配置。

原状：角色只能通过一个裸下拉选权限码，数据范围在另一个新增弹窗里，配置角色要开两处、且看不出权限属于哪个模块。

改为：角色行「配置」→ 一个弹窗内完成
  1) 角色名称 + 数据范围
  2) 权限按模块分组（iam/biz/fin/asset/ops/msg/sys/rpt/open/gov），每组可全选/清空
  3) 保存时同时提交角色信息与权限集合
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Rbac.vue')

DIALOG = '''
    <!-- 角色配置：基本信息 + 数据范围 + 权限，一页完成 -->
    <el-dialog v-model="roleCfgVisible" :title="`配置角色：${roleCfg.roleName || ''}`" width="760px">
      <el-form :model="roleCfg" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="角色编码">
            <el-input :model-value="roleCfg.roleCode" disabled /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="角色名称">
            <el-input v-model="roleCfg.roleName" data-testid="role-cfg-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="数据范围">
            <el-select v-model="roleCfg.dataScope" style="width:100%" data-testid="role-cfg-scope">
              <el-option label="全部数据 ALL" value="ALL" />
              <el-option label="本组织 ORG" value="ORG" />
              <el-option label="本组织及下级 ORG_SUB" value="ORG_SUB" />
              <el-option label="仅本人 SELF" value="SELF" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="状态">
            <el-select v-model="roleCfg.status" style="width:100%">
              <el-option label="启用" value="ENABLED" />
              <el-option label="停用" value="DISABLED" />
            </el-select></el-form-item></el-col>
        </el-row>
      </el-form>

      <div class="toolbar" style="margin:4px 0 8px">
        <b>权限配置</b>
        <span class="muted">已选 {{ checkedPerms.length }} / {{ perms.length }}</span>
        <div class="spacer" />
        <el-button size="small" @click="checkAllPerms">全选</el-button>
        <el-button size="small" @click="checkedPerms = []">清空</el-button>
      </div>

      <el-scrollbar max-height="380px">
        <div v-for="g in permGroups" :key="g.key" class="perm-group">
          <div class="perm-group-head">
            <el-checkbox
              :model-value="g.items.every((p) => checkedPerms.includes(String(p.id)))"
              :indeterminate="!g.items.every((p) => checkedPerms.includes(String(p.id)))
                && g.items.some((p) => checkedPerms.includes(String(p.id)))"
              @change="(v) => toggleGroup(g, v)">
              {{ g.label }}（{{ g.items.length }}）
            </el-checkbox>
          </div>
          <div class="perm-group-body">
            <el-checkbox
              v-for="p in g.items" :key="p.id"
              :model-value="checkedPerms.includes(String(p.id))"
              :label="`${p.permName}`"
              :title="p.permCode"
              @change="(v) => togglePerm(p, v)" />
          </div>
        </div>
      </el-scrollbar>

      <template #footer>
        <el-button @click="roleCfgVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRoleConfig">保存</el-button>
      </template>
    </el-dialog>
'''

CSS = '''
<style scoped>
.perm-group { border: 1px solid #ebeef5; border-radius: 4px; margin-bottom: 8px; }
.perm-group-head { background: #fafafa; padding: 6px 10px; border-bottom: 1px solid #ebeef5; }
.perm-group-body { padding: 8px 12px; display: flex; flex-wrap: wrap; gap: 6px 16px; }
</style>
'''

SCRIPT = '''
/** 角色配置：基本信息 + 数据范围 + 权限 一页完成 */
const MODULE_LABEL = {
  iam: '用户与权限', person: '人员与档案', biz: '业务办理', fin: '财务',
  asset: '资产房源', ops: '运维工单', msg: '消息待办', sys: '系统配置',
  rpt: '报表统计', open: '开放平台', gov: '监管报送', alloc: '配租轮候'
}
const roleCfgVisible = ref(false)
const roleCfg = reactive({ id: '', roleCode: '', roleName: '', dataScope: 'ALL', status: 'ENABLED' })
const checkedPerms = ref([])

/** 权限按模块分组（permCode 形如 biz:contract:create） */
const permGroups = computed(() => {
  const map = new Map()
  for (const p of perms.value) {
    const key = String(p.permCode || '').split(':')[0] || 'other'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(p)
  }
  return Array.from(map.entries())
    .map(([key, items]) => ({ key, label: MODULE_LABEL[key] || key, items }))
    .sort((a, b) => a.key.localeCompare(b.key))
})

function togglePerm(p, on) {
  const id = String(p.id)
  if (on) {
    if (!checkedPerms.value.includes(id)) checkedPerms.value = [...checkedPerms.value, id]
  } else {
    checkedPerms.value = checkedPerms.value.filter((x) => x !== id)
  }
}

function toggleGroup(g, on) {
  const ids = g.items.map((p) => String(p.id))
  if (on) {
    checkedPerms.value = Array.from(new Set([...checkedPerms.value, ...ids]))
  } else {
    checkedPerms.value = checkedPerms.value.filter((x) => !ids.includes(x))
  }
}

function checkAllPerms() {
  checkedPerms.value = perms.value.map((p) => String(p.id))
}

async function openRoleConfig(row) {
  roleCfg.id = row.id
  roleCfg.roleCode = row.roleCode
  roleCfg.roleName = row.roleName
  roleCfg.dataScope = row.dataScope || 'ALL'
  roleCfg.status = row.status || 'ENABLED'
  checkedPerms.value = []
  roleCfgVisible.value = true
  // 回显该角色已有权限
  try {
    const d = await req.get(`/rbac/roles/${row.id}/permissions`)
    const list = Array.isArray(d) ? d : (d?.rows || [])
    checkedPerms.value = list.map((x) => String(x.id || x))
  } catch (e) { /* 无回显接口时留空，由用户重选 */ }
}

async function saveRoleConfig() {
  if (!roleCfg.roleName) { ElMessage.warning('请填写角色名称'); return }
  saving.value = true
  try {
    await req.put(`/rbac/roles/${roleCfg.id}`, {
      roleName: roleCfg.roleName, dataScope: roleCfg.dataScope, status: roleCfg.status
    })
    await req.post(`/rbac/roles/${roleCfg.id}/permissions`, { ids: checkedPerms.value })
    ElMessage.success('角色配置已保存')
    roleCfgVisible.value = false
    load()
  } finally { saving.value = false }
}
'''


def main():
    s = io.open(P, encoding='utf-8').read()

    # 1) 角色行按钮：授权权限 → 配置
    s = s.replace('<el-button link type="primary" @click="openGrantPerms(row)">授权权限</el-button>',
                  '<el-button link type="primary" @click="openRoleConfig(row)" '
                  'data-testid="role-config">配置</el-button>', 1)

    # 2) 插入配置弹窗（放在授权关系弹窗之前）
    anchor = '    <!-- 授权关系 -->'
    if anchor in s and 'roleCfgVisible' not in s:
        s = s.replace(anchor, DIALOG + '\n' + anchor, 1)

    # 3) 插入脚本逻辑（放在 openGrantPerms 之前）
    anchor2 = 'function openGrantPerms(row) {'
    if anchor2 in s and 'function openRoleConfig' not in s:
        s = s.replace(anchor2, SCRIPT + '\n' + anchor2, 1)

    # 4) 补 computed 导入
    if 'computed' not in s.split('<script setup>')[1][:400]:
        s = s.replace("import { ref, reactive, onMounted, watch } from 'vue'",
                      "import { ref, reactive, computed, onMounted, watch } from 'vue'", 1)

    # 5) 补样式
    if '.perm-group' not in s:
        s = s.replace('</template>', '</template>\n' + CSS, 1)

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('Rbac.vue：角色配置弹窗已加入',
          '| 弹窗:', 'roleCfgVisible' in s,
          '| 脚本:', 'function openRoleConfig' in s)


if __name__ == '__main__':
    main()
