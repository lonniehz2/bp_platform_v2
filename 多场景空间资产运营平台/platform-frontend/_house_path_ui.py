import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read().replace("updateHouse: (houseId, body) => request(`/houses/${houseId}/update`", "updateHouse: (projectId, houseId, body) => request(`/projects/${projectId}/houses/${houseId}/update`")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Houses.vue'
s=io.open(p,encoding='utf-8').read().replace("await api.updateHouse(editing.value.id, { ...editForm })","await api.updateHouse(project.value.id, editing.value.id, { ...editForm })")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('house paths')
