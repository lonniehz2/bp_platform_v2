<template>
  <div>
    <div class="navbar"><span class="back" @click="$router.back()">←</span>我要报修</div>

    <div class="card">
      <el-form :model="form" label-position="top">
        <el-form-item label="问题类型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="水电" value="WATER_ELECTRIC" />
            <el-option label="门窗" value="DOOR_WINDOW" />
            <el-option label="墙面渗漏" value="LEAK" />
            <el-option label="家电" value="APPLIANCE" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="form.description" type="textarea" :rows="4"
                    placeholder="请描述具体情况，便于师傅带工具上门" />
        </el-form-item>
        <el-form-item label="紧急程度">
          <el-radio-group v-model="form.urgency">
            <el-radio value="NORMAL">一般</el-radio>
            <el-radio value="URGENT">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="saving"
                   @click="submit">提交报修</el-button>
      </el-form>
    </div>

    <div class="card">
      <b>提交说明</b>
      <div class="muted" style="margin-top:8px;line-height:1.7">
        · 报修会生成工单，并带 SLA 响应时限<br />
        · 紧急工单会同时通知值班人员<br />
        · 可在「我的」→ 待办 中查看处理进度
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { workOrderApi } from '@/api/modules'

const saving = ref(false)
const form = reactive({ type: 'WATER_ELECTRIC', description: '', urgency: 'NORMAL' })

async function submit() {
  if (!form.description) {
    ElMessage.warning('请填写问题描述')
    return
  }
  saving.value = true
  try {
    // 后端真实路径：POST /api/v1/workorders
    await workOrderApi.create({
      orderType: 'REPAIR',
      source: 'TENANT_APP',
      title: `住户报修：${form.type}`,
      description: form.description,
      priority: form.urgency,
      personId: localStorage.getItem('bp_person_id') || undefined
    })
    ElMessage.success('报修已提交')
    form.description = ''
  } catch (e) { /* 已提示 */ } finally {
    saving.value = false
  }
}
</script>
