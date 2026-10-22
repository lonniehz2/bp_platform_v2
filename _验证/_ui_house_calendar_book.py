# -*- coding: utf-8 -*-
"""酒店/民宿日房态：HouseCalendar 页增加「预订」「释放」操作与月历视图。

后端接口已具备：POST /house-calendar/book、/release、GET /{houseId}?month=
区间语义左闭右开 [checkIn, checkOut)。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'HouseCalendar.vue')
s = io.open(P, encoding='utf-8').read()
changed = []

# 1) 工具栏加「预订」「释放」
if 'openBook' not in s:
    m = re.search(r'(<el-button type="primary" @click="reload">按房源查</el-button>)', s)
    if m:
        s = s[:m.end()] + '''
      <el-button type="success" @click="openBook" data-testid="cal-book">预订</el-button>
      <el-button type="warning" plain @click="openRelease" data-testid="cal-release">释放</el-button>''' + s[m.end():]
        changed.append('工具栏')

# 2) 行内「预订此房」按钮
if 'bookForHouse(row)' not in s:
    s2 = re.sub(r'(<el-button link @click="openDetail\(row\)">详情</el-button>)',
                r'''<el-button link type="success" @click="bookForHouse(row)">预订</el-button>
            \1''', s, count=1)
    if s2 != s:
        s = s2
        changed.append('行内预订')

# 3) 弹窗
dialogs = '''
    <!-- 预订 -->
    <el-dialog v-model="bookVisible" title="预订房源（按日）" width="560px">
      <el-form :model="bf" label-width="100px">
        <el-form-item label="房源 ID" required>
          <el-input v-model="bf.houseId" placeholder="可从列表行点「预订」自动带入" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="入住日" required>
            <el-date-picker v-model="bf.checkIn" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="退房日" required>
            <el-date-picker v-model="bf.checkOut" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="占用类型">
            <el-select v-model="bf.targetStatus" style="width:100%">
              <el-option label="预订（BOOKED）" value="BOOKED" />
              <el-option label="直接入住（OCCUPIED）" value="OCCUPIED" />
            </el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="bf.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <el-alert type="info" :closable="false"
                title="区间左闭右开：11-01 入住、11-03 退房，占用 11-01 与 11-02 两晚" />
      <template #footer>
        <el-button @click="bookVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doBook">确认预订</el-button>
      </template>
    </el-dialog>

    <!-- 释放 -->
    <el-dialog v-model="releaseVisible" title="释放房态" width="520px">
      <el-form :model="rf" label-width="100px">
        <el-form-item label="房源 ID" required><el-input v-model="rf.houseId" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="起始日" required>
            <el-date-picker v-model="rf.checkIn" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日" required>
            <el-date-picker v-model="rf.checkOut" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="releaseVisible = false">取消</el-button>
        <el-button type="warning" :loading="saving" @click="doRelease">释放</el-button>
      </template>
    </el-dialog>
'''
if 'bookVisible' not in s:
    idx = s.rfind('</template>')
    s = s[:idx] + dialogs + s[idx:]
    changed.append('弹窗')

# 4) 脚本
script = '''
/** 日房态：预订 / 释放（酒店民宿场景） */
const bookVisible = ref(false)
const releaseVisible = ref(false)
const bf = reactive({ houseId: '', checkIn: '', checkOut: '', targetStatus: 'BOOKED', remark: '' })
const rf = reactive({ houseId: '', checkIn: '', checkOut: '' })

function openBook() {
  Object.assign(bf, { houseId: '', checkIn: '', checkOut: '', targetStatus: 'BOOKED', remark: '' })
  bookVisible.value = true
}

function bookForHouse(row) {
  openBook()
  bf.houseId = String(row.houseId || '')
  bf.checkIn = row.calendarDate || ''
}

function openRelease() {
  Object.assign(rf, { houseId: '', checkIn: '', checkOut: '' })
  releaseVisible.value = true
}

async function doBook() {
  if (!bf.houseId || !bf.checkIn || !bf.checkOut) {
    ElMessage.warning('请填写房源与起止日期'); return
  }
  saving.value = true
  try {
    const n = await req.post('/house-calendar/book', {
      houseId: bf.houseId, checkIn: bf.checkIn, checkOut: bf.checkOut,
      sourceType: 'MANUAL', targetStatus: bf.targetStatus, remark: bf.remark
    })
    ElMessage.success(`已锁定 ${n} 天`)
    bookVisible.value = false
    reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '预订失败（可能该区间已被占用）')
  } finally { saving.value = false }
}

async function doRelease() {
  if (!rf.houseId || !rf.checkIn || !rf.checkOut) {
    ElMessage.warning('请填写房源与起止日期'); return
  }
  saving.value = true
  try {
    const n = await req.post('/house-calendar/release', {
      houseId: rf.houseId, checkIn: rf.checkIn, checkOut: rf.checkOut
    })
    ElMessage.success(`已释放 ${n} 天`)
    releaseVisible.value = false
    reload()
  } finally { saving.value = false }
}
'''
if 'function openBook' not in s:
    anchor = 'onMounted('
    i = s.find(anchor)
    if i > 0:
        s = s[:i] + script + '\n' + s[i:]
        changed.append('脚本')

# 确保 ElMessage / reactive 可用
if 'from \'element-plus\'' not in s:
    s = s.replace("import { ref, onMounted } from 'vue'",
                  "import { ref, reactive, onMounted } from 'vue'\nimport { ElMessage } from 'element-plus'", 1)
elif "reactive" not in s.split('\n')[0:40].__str__():
    s = s.replace("import { ref, onMounted } from 'vue'",
                  "import { ref, reactive, onMounted } from 'vue'", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('HouseCalendar.vue 改动：', '、'.join(changed) if changed else '（无）')
