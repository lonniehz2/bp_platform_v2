import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'revokeGrant' not in s:
 s=s.replace("  createGrant: (body) => request('/grants', { method: 'POST', body: JSON.stringify(body) }),","  createGrant: (body) => request('/grants', { method: 'POST', body: JSON.stringify(body) }),\n  revokeGrant: (grantId, reason = '') => request(`/grants/${grantId}/revoke`, { method: 'POST', body: JSON.stringify({ reason }) }),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Devices.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const grantForm = reactive({ personId: '', targetId: '', validStart: '2026-11-08', validEnd: '2027-11-07' })","const grantForm = reactive({ personId: '', targetId: '', validStart: '2026-11-08', validEnd: '2027-11-07' })\nconst grants = ref([])")
s=s.replace("    if (!grantForm.targetId && s.length) grantForm.targetId = s[0].id\n  } catch (e) { error.value = e.message }","    if (!grantForm.targetId && s.length) grantForm.targetId = s[0].id\n    await loadGrants()\n  } catch (e) { error.value = e.message }")
s=s.replace("async function createGrant() {","async function loadGrants() {\n  if (!grantForm.personId) { grants.value = []; return }\n  try { grants.value = await api.grants(grantForm.personId) } catch { grants.value = [] }\n}\n\nasync function createGrant() {")
s=s.replace("    error.value = ''\n    alert('授权已创建')\n  } catch (e)","    error.value = ''\n    await loadGrants()\n    alert('授权已创建')\n  } catch (e)")
s=s.replace("onMounted(load)","async function revokeGrant(g) {\n  busy.value = true; error.value = ''\n  try { await api.revokeGrant(g.id, '页面撤销'); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }\n}\n\nonMounted(load)")
s=s.replace('''          <div class="field"><label>人员</label>
            <select v-model="grantForm.personId"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select>
          </div>''','''          <div class="field"><label>人员</label>
            <select v-model="grantForm.personId" @change="loadGrants"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select>
          </div>''')
s=s.replace('''          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="createGrant">新增授权</button></div>
        </div>
      </div>''','''          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="createGrant">新增授权</button></div>
        </div>
        <div v-if="grants.length" class="table-wrap" style="margin-top:12px">
          <table>
            <thead><tr><th>类型</th><th>授权对象</th><th>级别</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="g in grants" :key="g.id">
                <td>{{ g.targetType }}</td><td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
                <td class="small">{{ g.validStart }} ~ {{ g.validEnd || '长期' }}</td>
                <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
                <td><button v-if="g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revokeGrant(g)">撤销</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty">暂无授权</div>
      </div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('grant ui')
