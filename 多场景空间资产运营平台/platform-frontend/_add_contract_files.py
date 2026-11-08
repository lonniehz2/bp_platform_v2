import io
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const billForm = reactive({ contractId: '', periodStart: '2026-11-01', periodEnd: '2026-11-30', amount: 1200 })","const billForm = reactive({ contractId: '', periodStart: '2026-11-01', periodEnd: '2026-11-30', amount: 1200 })\nconst selectedContract = ref(null)\nconst files = ref([])\nconst fileBusy = ref(false)")
s=s.replace("async function generateBill() {","async function openFiles(c) {\n  selectedContract.value = c\n  files.value = await api.files('CONTRACT', c.id)\n}\n\nasync function uploadFile(e) {\n  const file = e.target.files?.[0]\n  if (!file || !selectedContract.value) return\n  fileBusy.value = true; error.value = ''\n  try {\n    await api.uploadFile('CONTRACT', selectedContract.value.id, file)\n    files.value = await api.files('CONTRACT', selectedContract.value.id)\n    e.target.value = ''\n  } catch (err) { error.value = err.message } finally { fileBusy.value = false }\n}\n\nasync function downloadFile(f) {\n  try { await api.downloadFile(f.id, f.fileName) } catch (e) { error.value = e.message }\n}\n\nasync function generateBill() {")
s=s.replace('''            <thead><tr><th>合同编号</th><th>房屋</th><th>承租人</th><th>租金</th><th>押金</th><th>状态</th></tr></thead>''','''            <thead><tr><th>合同编号</th><th>房屋</th><th>承租人</th><th>租金</th><th>押金</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''                <td><span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span></td>
              </tr>''','''                <td><span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span></td>
                <td><button class="sm" @click="openFiles(c)">附件</button></td>
              </tr>''')
s=s.replace('''      <div class="panel">
        <div class="panel-head"><h2>生成租金账单</h2>''','''      <div v-if="selectedContract" class="panel">
        <div class="panel-head"><h2>合同附件</h2><span class="small muted">{{ selectedContract.contractNo }}</span></div>
        <div class="row" style="margin-bottom:10px">
          <input type="file" @change="uploadFile" :disabled="fileBusy" style="max-width:320px" />
        </div>
        <div v-if="!files.length" class="empty">暂无附件</div>
        <div v-for="f in files" :key="f.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ f.fileName }}</div><div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div>
          <button class="sm" @click="downloadFile(f)">下载</button>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>生成租金账单</h2>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('contract files')
