# -*- coding: utf-8 -*-
"""三处修复：
  8) 日房态：房源 ID → 房源名称模糊搜索下拉
  9) 实名核验：人员 ID → 姓名搜索；图片 URL → 本地上传
  1) 组织机构：社区/村 候选按街道过滤 + 明确提示
"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')

# ---------------- 8) 日房态 ----------------
P = os.path.join(V, 'views', 'HouseCalendar.vue')
s = io.open(P, encoding='utf-8').read()
OLD = """      <el-input v-model="houseId" placeholder="房源ID"
                style="width:210px" />
      <el-button type="primary" @click="reload">按房源查</el-button>"""
NEW = """      <el-select v-model="houseId" placeholder="输入房源名称搜索" filterable remote clearable
                 :remote-method="searchHouses" :loading="houseSearching"
                 style="width:260px" @change="onHousePicked">
        <el-option v-for="h in houseOptions" :key="h.id"
                   :label="(h.houseName || h.houseCode) + ' · ' + (h.houseCode || '')"
                   :value="h.id" />
      </el-select>
      <el-button type="primary" @click="reload">按房源查</el-button>"""
if OLD in s and 'searchHouses' not in s:
    s = s.replace(OLD, NEW, 1)
    s = s.replace("""const houseLabel = ref('')""",
                  """const houseLabel = ref('')
const houseOptions = ref([])
const houseSearching = ref(false)

/** 房源名称模糊搜索（下拉候选） */
async function searchHouses(kw) {
  houseSearching.value = true
  try {
    const d = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 30, keyword: kw || undefined }
    })
    houseOptions.value = (d.rows || d || []).map((h) => ({
      id: h.id, houseName: h.houseName, houseCode: h.houseCode
    }))
  } catch (e) {
    houseOptions.value = []
  } finally {
    houseSearching.value = false
  }
}

function onHousePicked(id) {
  const hit = houseOptions.value.find((h) => String(h.id) === String(id))
  houseLabel.value = hit ? (hit.houseName || hit.houseCode) : ''
  reload()
}""", 1)
    # 首次进入预载候选
    s = s.replace("""onMounted(""", """onMounted(async () => {
  await searchHouses('')
  pageInit()
})

function pageInit(""", 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('日房态：房源下拉已加')
else:
    print('日房态：跳过')

# ---------------- 9) 实名核验 ----------------
P = os.path.join(V, 'views', 'Persons.vue')
s = io.open(P, encoding='utf-8').read()
OLD_VERIFY = """        <el-form-item label="人员ID" required>
          <el-input v-model="vf.personId" /></el-form-item>"""
NEW_VERIFY = """        <el-form-item label="人员" required>
          <PersonPicker v-model="vf.personId" width="260px" testid="verify-person-picker" />
        </el-form-item>"""
if OLD_VERIFY in s and 'verify-person-picker' not in s:
    s = s.replace(OLD_VERIFY, NEW_VERIFY, 1)

OLD_IMGS = """        <el-form-item label="人脸图片URL">
          <el-input v-model="vf.faceImgUrl" /></el-form-item>
        <el-form-item label="证件图片URL">
          <el-input v-model="vf.idcardImgUrl" /></el-form-item>"""
NEW_IMGS = """        <el-form-item label="人脸照片">
          <div style="width:100%">
            <el-upload :action="uploadAction" :headers="uploadHeaders" name="file"
                       :show-file-list="false" accept="image/*"
                       :on-success="(r) => { vf.faceImgUrl = fileUrlOf(r) }"
                       :on-error="() => ElMessage.error('上传失败')">
              <el-button size="small">本地上传</el-button>
            </el-upload>
            <div class="muted" style="font-size:12px;margin-top:4px">
              {{ vf.faceImgUrl || '未上传（也可粘贴外部 URL）' }}
            </div>
            <el-input v-model="vf.faceImgUrl" placeholder="或粘贴图片 URL" size="small" />
          </div>
        </el-form-item>
        <el-form-item label="证件照片">
          <div style="width:100%">
            <el-upload :action="uploadAction" :headers="uploadHeaders" name="file"
                       :show-file-list="false" accept="image/*"
                       :on-success="(r) => { vf.idcardImgUrl = fileUrlOf(r) }"
                       :on-error="() => ElMessage.error('上传失败')">
              <el-button size="small">本地上传</el-button>
            </el-upload>
            <div class="muted" style="font-size:12px;margin-top:4px">
              {{ vf.idcardImgUrl || '未上传（也可粘贴外部 URL）' }}
            </div>
            <el-input v-model="vf.idcardImgUrl" placeholder="或粘贴图片 URL" size="small" />
          </div>
        </el-form-item>"""
if OLD_IMGS in s:
    s = s.replace(OLD_IMGS, NEW_IMGS, 1)

if 'fileUrlOf' not in s.split('</script>')[0]:
    s = s.replace("import req from '@/api/request'",
                  "import req, { getToken, getTenant } from '@/api/request'\n"
                  "import PersonPicker from '@/components/PersonPicker.vue'", 1)
    s = s.replace("""const verifyVisible = ref(false)""",
                  """const verifyVisible = ref(false)
// 核验照片上传：走后端 /files/upload，成功回填可访问 URL
const uploadAction = '/api/v1/files/upload?bizType=PERSON_VERIFY'
const uploadHeaders = {
  Authorization: `Bearer ${getToken()}`,
  'X-Tenant-Id': getTenant()
}
function fileUrlOf(r) {
  const f = (r && r.data) || {}
  return f.id ? `/api/v1/files/${f.id}/download` : ''
}""", 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('实名核验：人员选择 + 图片上传已加')

# ---------------- 1) 组织机构社区 ----------------
P = os.path.join(V, 'views', 'Orgs.vue')
s = io.open(P, encoding='utf-8').read()
OLD_C = """  // 合并历史输入，便于复用
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    ;(d.rows || d || []).forEach((o) => o.community && set.add(o.community))
  } catch (e) { /* 忽略 */ }"""
NEW_C = """  // 合并历史输入：优先同街道，其次全部（便于复用已录入社区名）
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    const all = d.rows || d || []
    const sameStreet = all.filter((o) => !streetCode || o.streetCode === streetCode)
    sameStreet.forEach((o) => o.community && set.add(o.community))
    if (!set.size) {
      all.forEach((o) => o.community && set.add(o.community))
    }
  } catch (e) { /* 忽略 */ }"""
if OLD_C in s:
    s = s.replace(OLD_C, NEW_C, 1)
    # 提示文案
    s = s.replace("""placeholder="社区/村（可手填）" """, """placeholder="可手工输入社区/村" """)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('组织机构：社区候选按街道过滤')
