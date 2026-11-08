import io
p=r'src\pages\Projects.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref } from 'vue'")
s=s.replace("import { api } from '../api'","import { api } from '../api'\nimport { can } from '../permissions'\nimport Pager from '../components/Pager.vue'")
s=s.replace("const modes = ref([])","const modes = ref([])\nconst page = ref(1)")
s=s.replace("const form = reactive","const pagedProjects = computed(() => projects.value.slice((page.value - 1) * 10, page.value * 10))\nconst form = reactive")
s=s.replace('<tr v-for="p in projects" :key="p.id">','<tr v-for="p in pagedProjects" :key="p.id">')
s=s.replace('''          </table>
        </div>
      </div>
    </div>
  </div>
</template>''','''          </table>
        </div>
        <Pager :total="projects.length" :page="page" @update:page="page = $event" />
      </div>
    </div>
  </div>
</template>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('projects pager')
