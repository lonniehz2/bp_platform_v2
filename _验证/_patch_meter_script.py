# -*- coding: utf-8 -*-
"""补抄表脚本（设备/批量/导入）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'MeterReadings.vue')
s = io.open(p, encoding='utf-8').read()

if 'const devices = ref' not in s:
    s = s.replace(
        "const rf = reactive({ houseId: '', feeItemId: '', reading: '', readDate: '', deviceId: '' })",
        "const rf = reactive({ houseId: '', feeItemId: '', reading: '', readDate: '', deviceId: '' })\n"
        "const devices = ref([])\n"
        "const deviceRows = ref([])\n"
        "const batchVisible = ref(false)\n"
        "const batchRows = ref([])\n"
        "const batchResult = ref(null)\n\n"
        "async function loadDevices() {\n"
        "  devices.value = []\n"
        "  deviceRows.value = []\n"
        "  if (!rf.houseId || !rf.feeItemId) return\n"
        "  try {\n"
        "    const list = await req.get('/fin/meter-readings/devices',\n"
        "      { params: { houseId: rf.houseId, feeItemId: rf.feeItemId } })\n"
        "    devices.value = list || []\n"
        "    deviceRows.value = (list || []).map((d) => ({ ...d, reading: '' }))\n"
        "  } catch (e) { devices.value = [] }\n"
        "}\n\n"
        "function openBatch() {\n"
        "  batchRows.value = []\n"
        "  batchResult.value = null\n"
        "  addBatchRow()\n"
        "  batchVisible.value = true\n"
        "}\n\n"
        "function addBatchRow() {\n"
        "  batchRows.value.push({ houseId: query.houseId || '', feeItemId: query.feeItemId || '',\n"
        "    deviceId: '', reading: '', readDate: new Date().toISOString().slice(0, 10) })\n"
        "}\n\n"
        "function downloadTemplate() {\n"
        "  const csv = '\\ufeff房源编号,计量项目,设备编号,读数,抄表日期\\n'\n"
        "    + 'H8063501,电费,DEMO-ELEC-00001,1200.5,2026-10-28\\n'\n"
        "  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })\n"
        "  const a = document.createElement('a')\n"
        "  a.href = URL.createObjectURL(blob)\n"
        "  a.download = '抄表导入模板.csv'\n"
        "  a.click()\n"
        "  URL.revokeObjectURL(a.href)\n"
        "}\n\n"
        "function parseCsv(text) {\n"
        "  const rows = []\n"
        "  text.replace(/^\\ufeff/, '').split(/\\r?\\n/).forEach((line) => {\n"
        "    if (!line.trim()) return\n"
        "    rows.push(line.split(',').map((x) => x.trim().replace(/^\"|\"$/g, '')))\n"
        "  })\n"
        "  return rows\n"
        "}\n\n"
        "function onCsv(file) {\n"
        "  const reader = new FileReader()\n"
        "  reader.onload = (e) => {\n"
        "    const all = parseCsv(String(e.target.result || ''))\n"
        "    if (!all.length) { ElMessage.warning('文件为空'); return }\n"
        "    const body = /房源编号/.test(all[0].join(',')) ? all.slice(1) : all\n"
        "    batchRows.value = body.map((c) => {\n"
        "      const house = houses.value.find((h) => String(h.houseCode) === c[0]\n"
        "        || String(h.houseName) === c[0])\n"
        "      const item = meterItems.value.find((m) => m.itemName === c[1]\n"
        "        || String(m.itemCode) === c[1])\n"
        "      return { houseId: house ? house.id : '', feeItemId: item ? item.id : '',\n"
        "        deviceId: c[2] || '', reading: c[3] || '', readDate: c[4] || '' }\n"
        "    })\n"
        "    ElMessage.success('已解析 ' + batchRows.value.length + ' 行，请核对后提交')\n"
        "  }\n"
        "  reader.readAsText(file.raw, 'utf-8')\n"
        "}\n\n"
        "async function doBatch() {\n"
        "  const cmds = batchRows.value.filter((r) => r.houseId && r.feeItemId && r.reading !== '')\n"
        "    .map((r) => ({ houseId: r.houseId, feeItemId: r.feeItemId,\n"
        "      deviceId: r.deviceId || undefined, reading: Number(r.reading),\n"
        "      readDate: r.readDate || undefined }))\n"
        "  if (!cmds.length) { ElMessage.warning('没有可提交的行'); return }\n"
        "  saving.value = true\n"
        "  try {\n"
        "    batchResult.value = await req.post('/fin/meter-readings/batch', cmds)\n"
        "    ElMessage.success('提交完成：成功 ' + batchResult.value.created\n"
        "      + '，失败 ' + batchResult.value.failed)\n"
        "    load()\n"
        "  } catch (e) {\n"
        "    ElMessage.error(e?.response?.data?.message || '批量提交失败')\n"
        "  } finally { saving.value = false }\n"
        "}", 1)
    print('  ✔ 脚本注入')

s = s.replace('''function openRecord() {
  Object.assign(rf, { houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    reading: '', readDate: new Date().toISOString().slice(0, 10), deviceId: '' })
  recordVisible.value = true
}''', '''function openRecord() {
  Object.assign(rf, { houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    reading: '', readDate: new Date().toISOString().slice(0, 10), deviceId: '' })
  devices.value = []
  deviceRows.value = []
  recordVisible.value = true
  loadDevices()
}''', 1)

s = s.replace('''async function doRecord() {
  if (!rf.houseId || !rf.feeItemId || rf.reading === '') {
    ElMessage.warning('请填写房源、计量项目与本次读数'); return
  }
  saving.value = true
  try {
    await req.post('/fin/meter-readings', {
      houseId: rf.houseId, feeItemId: rf.feeItemId,
      reading: Number(rf.reading), readDate: rf.readDate || undefined,
      deviceId: rf.deviceId || undefined
    })
    ElMessage.success('读数已录入')
    recordVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '录入失败')
  } finally { saving.value = false }
}''', '''async function doRecord() {
  if (!rf.houseId || !rf.feeItemId) {
    ElMessage.warning('请选择房源与计量项目'); return
  }
  let cmds = []
  if (deviceRows.value.length) {
    cmds = deviceRows.value.filter((d) => d.reading !== '' && d.reading != null)
      .map((d) => ({ houseId: rf.houseId, feeItemId: rf.feeItemId,
        deviceId: d.deviceId, reading: Number(d.reading),
        readDate: rf.readDate || undefined }))
    if (!cmds.length) { ElMessage.warning('请至少填写一台设备的读数'); return }
  } else {
    if (rf.reading === '') { ElMessage.warning('请填写本次读数'); return }
    cmds = [{ houseId: rf.houseId, feeItemId: rf.feeItemId,
      deviceId: rf.deviceId || undefined, reading: Number(rf.reading),
      readDate: rf.readDate || undefined }]
  }
  saving.value = true
  try {
    const r = await req.post('/fin/meter-readings/batch', cmds)
    ElMessage.success('录入完成：成功 ' + r.created + '，失败 ' + r.failed)
    recordVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '录入失败')
  } finally { saving.value = false }
}''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('MeterReadings 脚本已补')
