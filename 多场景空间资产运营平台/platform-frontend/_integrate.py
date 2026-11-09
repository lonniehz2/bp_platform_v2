import io
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { navGroups, navItems } from './navConfig'","import { navGroups, navItems } from './navConfig'\nimport SearchSelect from './components/SearchSelect.vue'")
s=s.replace('''          <select v-model="currentProjectId" @change="switchProject" class="project-select">
            <option value="">{{ t('common.project') }}</option>
            <option v-for="p in projects" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option>
          </select>''','''          <SearchSelect
            v-model="currentProjectId"
            :options="projects"
            label-key="orgName"
            sublabel-key="orgCode"
            value-key="id"
            placeholder="选择项目"
            class="project-picker"
            @change="switchProject"
          />''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\DeviceBinding.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { can } from '../permissions'","import { can } from '../permissions'\nimport TreeSelect from '../components/TreeSelect.vue'")
s=s.replace('''<select v-model="form.spaceId"><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}（{{ s.spaceType }}）</option></select>''','''<TreeSelect v-model="form.spaceId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" placeholder="选择绑定空间" />''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.project-picker' not in s:
 s += '\n.project-picker { width: 260px; flex: 0 0 260px; }\n@media (max-width: 760px) { .project-picker { width: 100%; flex: 1 1 100%; } }\n'
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('integrate selectors')
