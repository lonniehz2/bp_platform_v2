import { defineStore } from 'pinia'
import { ref } from 'vue'
import req from '@/api/request'

/** 物业项目上下文：选中项目后，后续资产/收费/报表按项目过滤。 */
export const usePropertyStore = defineStore('property', () => {
  const projects = ref([])
  const projectId = ref(localStorage.getItem('property-project-id') || '')
  const loading = ref(false)

  async function loadProjects() {
    loading.value = true
    try {
      projects.value = await req.get('/property/projects') || []
      if (!projectId.value && projects.value.length) {
        projectId.value = String(projects.value[0].orgId)
      }
      if (projectId.value && !projects.value.some((p) => String(p.orgId) === String(projectId.value))) {
        projectId.value = projects.value.length ? String(projects.value[0].orgId) : ''
      }
      persist()
      return projects.value
    } finally {
      loading.value = false
    }
  }

  function selectProject(id) {
    projectId.value = id == null ? '' : String(id)
    persist()
  }

  function persist() {
    if (projectId.value) localStorage.setItem('property-project-id', projectId.value)
    else localStorage.removeItem('property-project-id')
  }

  function currentProject() {
    return projects.value.find((p) => String(p.orgId) === String(projectId.value)) || null
  }

  return { projects, projectId, loading, loadProjects, selectProject, currentProject }
})
