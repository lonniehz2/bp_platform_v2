# -*- coding: utf-8 -*-
"""补齐剩余 7 个模块写操作：消息/规则/开放/RBAC/授权/日房态"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'


def patch(file, marker, insert_actions=None, insert_toolbar=None,
          insert_tpl_tail=None, insert_script=None, imports=None):
    p = os.path.join(V, file)
    s = io.open(p, encoding='utf-8').read()
    if marker in s:
        print('  - %s 已含 %s' % (file, marker))
        return
    changed = False
    if insert_toolbar and insert_toolbar[0] in s:
        s = s.replace(insert_toolbar[0], insert_toolbar[0] + insert_toolbar[1], 1)
        changed = True
    if insert_actions and insert_actions[0] in s:
        s = s.replace(insert_actions[0],
                      insert_actions[1] + insert_actions[0], 1)
        changed = True
    if insert_tpl_tail and insert_tpl_tail[0] in s:
        s = s.replace(insert_tpl_tail[0],
                      insert_tpl_tail[1] + insert_tpl_tail[0], 1)
        changed = True
    if insert_script and insert_script[0] in s:
        s = s.replace(insert_script[0], insert_script[1] + insert_script[0], 1)
        changed = True
    if imports:
        for old, new in imports:
            if old in s and new not in s:
                s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  %s %s' % ('✓' if changed else '!', file))


# ================= 1) 消息待办：标记已读/已办/发送/广播 =================
MSG_TB = '''      <el-button type="success" @click="sendVisible = true">发送消息</el-button>
      <el-button @click="broadcast">批量广播</el-button>
      <el-button @click="retry">重推失败</el-button>
'''
MSG_ACT = '''          <el-button link type="primary" @click="markRead(row)">已读</el-button>
          <el-button link type="success" @click="markDone(row)">办结</el-button>
'''
MSG_TPL = '''    <el-dialog v-model="sendVisible" title="发送消息" width="560px">
      <el-form :model="mf" label-width="110px">
        <el-form-item label="模板编码" required>
          <el-input v-model="mf.templateCode" placeholder="如 CONTRACT_EFFECTIVE" />
        </el-form-item>
        <el-form-item label="业务类型">
          <el-input v-model="mf.bizType" placeholder="如 CONTRACT" /></el-form-item>
        <el-form-item label="业务ID">
          <el-input v-model.number="mf.bizId" /></el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="mf.channel" style="width:100%">
            <el-option label="站内信" value="INNER" />
            <el-option label="短信" value="SMS" />
            <el-option label="微信" value="WECHAT" />
            <el-option label="APP推送" value="PUSH" />
          </el-select></el-form-item>
        <el-form-item label="接收人类型">
          <el-select v-model="mf.receiverType" style="width:100%">
            <el-option label="人员" value="PERSON" />
            <el-option label="用户" value="USER" />
            <el-option label="组织" value="ORG" />
          </el-select></el-form-item>
        <el-form-item label="接收人ID">
          <el-input v-model="mf.receiverId" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="mf.title" /></el-form-item>
        <el-form-item label="内容">
          <el-input v-model="mf.content" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSend">发送</el-button>
      </template>
    </el-dialog>
'''
MSG_SCRIPT = '''
async function markRead(row) {
  await req.post(`/messages/todos/${row.id}/read`)
  ElMessage.success('已标记已读'); load()
}
async function markDone(row) {
  await req.post(`/messages/todos/${row.id}/done`)
  ElMessage.success('已办结'); load()
}
async function broadcast() {
  const { value } = await ElMessageBox.prompt('广播内容', '批量广播')
  await req.post('/messages/broadcast',
    { bizType: 'SYSTEM', title: '系统通知', content: value, bizId: 0 })
  ElMessage.success('已广播')
}
async function retry() {
  const r = await req.post('/messages/retry-failed', null, { params: { limit: 20 } })
  ElMessage.success('重推完成：' + (r?.count ?? '已执行'))
}
async function doSend() {
  if (!mf.templateCode) { ElMessage.warning('请填写模板编码'); return }
  saving.value = true
  try {
    await req.post('/messages/send', { ...mf })
    ElMessage.success('已发送'); sendVisible.value = false
  } finally { saving.value = false }
}
'''
patch('Messages.vue', 'sendVisible',
      insert_toolbar=('      <div class="spacer" />', '\n' + MSG_TB) if False else None,
      insert_tpl_tail=('</template>', MSG_TPL),
      insert_script=('</script>', MSG_SCRIPT),
      imports=[("import { ref, onMounted }", "import { ref, reactive, onMounted }"),
               ("import { ref, reactive, onMounted } from 'vue'",
                "import { ref, reactive, onMounted } from 'vue'\n"
                "import { ElMessage, ElMessageBox } from 'element-plus'\n"
                "import req from '@/api/request'")])

# 若上面 toolbar 未插入，单独插
p = os.path.join(V, 'Messages.vue')
s = io.open(p, encoding='utf-8').read()
if 'sendVisible = true' not in s:
    s = s.replace('      <div class="spacer" />',
                  '      <div class="spacer" />\n' + MSG_TB, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ Messages.vue 工具栏按钮')

if 'const sendVisible' not in s:
    s = io.open(p, encoding='utf-8').read()
    s = s.replace("const show = ref(false)",
                  "const show = ref(false)\nconst sendVisible = ref(false)\n"
                  "const saving = ref(false)\n"
                  "const mf = reactive({ templateCode: '', bizType: '', bizId: null,\n"
                  "  channel: 'INNER', receiverType: 'PERSON', receiverId: '',\n"
                  "  title: '', content: '' })", 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ Messages.vue 状态对象')

print('\n--- 其余模块用统一追加式补丁 ---')
