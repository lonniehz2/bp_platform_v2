import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'changePassword' not in s:
 s=s.replace("  login: (body) => request('/auth/login', { method: 'POST', body: JSON.stringify(body) }),","  login: (body) => request('/auth/login', { method: 'POST', body: JSON.stringify(body) }),\n  changePassword: (body) => request('/auth/password', { method: 'POST', body: JSON.stringify(body) }),")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const currentUser = computed(() => {","const pwdOpen = ref(false)\nconst pwdError = ref('')\nconst pwd = reactive({ oldPassword: '', newPassword: '', confirm: '' })\nconst currentUser = computed(() => {")
s=s.replace("import { computed, onMounted, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'")
s=s.replace("function logout() {","async function changePassword() {\n  pwdError.value = ''\n  if (!pwd.oldPassword || pwd.newPassword.length < 6) { pwdError.value = '请输入原密码，新密码至少 6 位'; return }\n  if (pwd.newPassword !== pwd.confirm) { pwdError.value = '两次新密码不一致'; return }\n  try {\n    await api.changePassword({ oldPassword: pwd.oldPassword, newPassword: pwd.newPassword })\n    pwdOpen.value = false\n    pwd.oldPassword = ''; pwd.newPassword = ''; pwd.confirm = ''\n    alert('密码已修改')\n  } catch (e) { pwdError.value = e.message }\n}\n\nfunction logout() {")
s=s.replace('''          <button class="sm" @click="logout">{{ t('common.logout') }}</button>''','''          <button class="sm" @click="pwdOpen = true">修改密码</button>
          <button class="sm" @click="logout">{{ t('common.logout') }}</button>''')
s=s.replace('''    </main>
  </div>
</template>''','''    </main>

    <div v-if="pwdOpen" class="modal-mask" @click.self="pwdOpen = false">
      <div class="modal">
        <div class="panel-head"><h2>修改密码</h2><button class="sm" @click="pwdOpen = false">关闭</button></div>
        <div v-if="pwdError" class="error">{{ pwdError }}</div>
        <div class="field"><label>原密码</label><input v-model="pwd.oldPassword" type="password" /></div>
        <div class="field"><label>新密码（至少 6 位）</label><input v-model="pwd.newPassword" type="password" /></div>
        <div class="field"><label>确认新密码</label><input v-model="pwd.confirm" type="password" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" @click="changePassword">保存</button></div>
      </div>
    </div>
  </div>
</template>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('password modal')
