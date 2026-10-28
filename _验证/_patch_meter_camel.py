# -*- coding: utf-8 -*-
"""设备字段统一转 camelCase，修复单条表格空白。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'MeterReadings.vue')
s = io.open(p, encoding='utf-8').read()


def rep(old, new, label):
    global s
    if old not in s:
        print('  ! 未匹配:', label)
        return
    s = s.replace(old, new, 1)
    print('  ✔', label)


rep('''    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: rf.houseId, feeItemId: rf.feeItemId } })
    devices.value = list || []
    deviceRows.value = (list || []).map((d) => ({ ...d, reading: '' }))''',
    '''    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: rf.houseId, feeItemId: rf.feeItemId } })
    // 后端返回 snake_case，前端表格用 camelCase
    const mapped = (list || []).map((d) => ({
      deviceId: d.device_id,
      deviceName: d.device_name,
      deviceType: d.device_type,
      spaceName: d.space_name
    }))
    devices.value = mapped
    deviceRows.value = mapped.map((d) => ({ ...d, reading: '' }))''', '单条设备映射')

rep('''    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: row.houseId, feeItemId: row.feeItemId } })
    row.devices = list || []
    if (row.devices.length === 1) {
      row.deviceId = row.devices[0].device_id
      row.deviceName = row.devices[0].device_name
      row.deviceType = row.devices[0].device_type
    } else if (row.devices.length > 1) {
      row.deviceId = row.devices[0].device_id
      row.deviceName = row.devices[0].device_name
      row.deviceType = row.devices[0].device_type
    }''',
    '''    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: row.houseId, feeItemId: row.feeItemId } })
    row.devices = (list || []).map((d) => ({
      deviceId: d.device_id,
      deviceName: d.device_name,
      deviceType: d.device_type,
      spaceName: d.space_name
    }))
    if (row.devices.length) {
      row.deviceId = row.devices[0].deviceId
      row.deviceName = row.devices[0].deviceName
      row.deviceType = row.devices[0].deviceType
    }''', '批量设备映射')

rep('''function pickDevice(row) {
  const d = (row.devices || []).find((x) => x.device_id === row.deviceId)
  row.deviceName = d ? d.device_name : ''
  row.deviceType = d ? d.device_type : ''
}''',
    '''function pickDevice(row) {
  const d = (row.devices || []).find((x) => x.deviceId === row.deviceId)
  row.deviceName = d ? d.deviceName : ''
  row.deviceType = d ? d.deviceType : ''
}''', '批量选择设备')

rep('''              <el-option v-for="d in row.devices" :key="d.device_id"
                         :label="d.device_id" :value="d.device_id" />''',
    '''              <el-option v-for="d in row.devices" :key="d.deviceId"
                         :label="d.deviceId" :value="d.deviceId" />''', '批量下拉字段')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('MeterReadings 设备字段已统一')
