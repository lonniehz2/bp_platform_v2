import io
p=r'src\components\DataTable.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''          <tr v-for="row in rows" v-else :key="row[rowKey]" @click="$emit('rowClick', row)">
            <td v-if="selectable" class="dt-check" @click.stop><input type="checkbox" :checked="selected.has(String(row[rowKey]))" @change="toggleRow(row)" /></td>
            <td v-for="c in columns" :key="c.key" :style="{ textAlign: c.align || 'left' }">
              <slot :name="'cell-' + c.key" :row="row" :value="row[c.key]">{{ cell(row, c) }}</slot>
            </td>
          </tr>''','''          <template v-else>
            <tr v-for="row in rows" :key="row[rowKey]" @click="$emit('rowClick', row)">
              <td v-if="selectable" class="dt-check" @click.stop><input type="checkbox" :checked="selected.has(String(row[rowKey]))" @change="toggleRow(row)" /></td>
              <td v-for="c in columns" :key="c.key" :style="{ textAlign: c.align || 'left' }">
                <slot :name="'cell-' + c.key" :row="row" :value="row[c.key]">{{ cell(row, c) }}</slot>
              </td>
            </tr>
          </template>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fix v-else')
