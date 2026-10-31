# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\views\Energy.vue'
s = io.open(p, encoding='utf-8').read()

s = s.replace('''        <div class="toolbar">
          <el-input v-model="period" placeholder="2026-10" style="width:120px" />
          <el-button type="primary" @click="loadAnalysis">查询</el-button>
        </div>''','''        <div class="toolbar">
          <el-input v-model="period" placeholder="2026-10" style="width:120px" />
          <el-select v-model="analysisItem" placeholder="收费项目" clearable style="width:200px">
            <el-option v-for="f in feeItems" :key="f.id" :label="f.itemName" :value="String(f.id)" />
          </el-select>
          <el-button type="primary" @click="loadAnalysis">查询</el-button>
        </div>''', 1)

s = s.replace('''        <el-form-item label="名称"><el-input v-model="pf.meterName" /></el-form-item>''',
              '''        <el-form-item label="床位容量">
          <el-input v-model.number="pf.bedCapacity" placeholder="房间床位数" />
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="pf.meterName" /></el-form-item>''', 1)

s = s.replace("const stat = ref(null)", "const stat = ref(null)\nconst analysisItem = ref('')", 1)
s = s.replace("const pf = reactive({ spaceId: '', feeItemId: '', meterName: '', meterScope: 'ROOM' })",
              "const pf = reactive({ spaceId: '', feeItemId: '', bedCapacity: null, meterName: '', meterScope: 'ROOM' })", 1)
s = s.replace("Object.assign(pf, { spaceId: '', feeItemId: '', meterName: '', meterScope: 'ROOM' })",
              "Object.assign(pf, { spaceId: '', feeItemId: '', bedCapacity: null, meterName: '', meterScope: 'ROOM' })", 1)
s = s.replace("stat.value = await req.get('/fin/energy-analysis/monthly', { params: { period: period.value } })",
              "stat.value = await req.get('/fin/energy-analysis/monthly', { params: { period: period.value, feeItemId: analysisItem.value || undefined } })", 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Energy UI updated')
