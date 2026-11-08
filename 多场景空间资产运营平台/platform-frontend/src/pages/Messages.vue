<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const messages = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ title: '', content: '', bizType: '', bizId: '' })
const unread = computed(() => messages.value.filter(m => m.readStatus === 'UNREAD').length)

async function load() {
  error.value = ''
  try { messages.value = await api.messages() } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error('请填写消息标题')
    await api.createMessage({ userId: null, title: form.title.trim(), content: form.content, bizType: form.bizType, bizId: form.bizId })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function read(m) {
  try { await api.readMessage(m.id); await load() } catch (e) { error.value = e.message }
}

async function readAll() {
  try { await api.readAllMessages(); await load() } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>消息中心</h2><p>系统通知、业务提醒和待办消息</p></div>
        <div class="row"><span class="badge" :class="unread ? 'orange' : 'green'">未读 {{ unread }}</span><button class="sm" @click="readAll">全部已读</button></div>
      </div>
      <div class="row">
        <div class="field" style="flex:2"><label>标题</label><input v-model="form.title" /></div>
        <div class="field"><label>业务类型</label><input v-model="form.bizType" placeholder="CONTRACT/BILL" /></div>
        <div class="field"><label>业务ID</label><input v-model="form.bizId" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">发布消息</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>内容</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>消息列表</h2><span class="small muted">{{ messages.length }} 条</span></div>
      <div v-if="!messages.length" class="empty">暂无消息</div>
      <div v-for="m in messages" :key="m.id" class="row" style="padding:12px 0;border-bottom:1px solid var(--line);align-items:flex-start">
        <div style="flex:1">
          <div style="font-weight:500">{{ m.title }} <span v-if="m.readStatus === 'UNREAD'" class="badge orange">未读</span></div>
          <div class="small muted" style="margin-top:4px">{{ m.content || '-' }}</div>
          <div class="small muted" style="margin-top:4px">{{ m.createTime }} {{ m.bizType ? '· ' + m.bizType : '' }} {{ m.bizId || '' }}</div>
        </div>
        <button v-if="m.readStatus === 'UNREAD'" class="sm" @click="read(m)">标记已读</button>
      </div>
    </div>
  </div>
</template>
