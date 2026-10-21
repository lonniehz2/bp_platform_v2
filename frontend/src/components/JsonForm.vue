<template>
  <el-form :model="model" label-width="110px" size="default" class="json-form">
    <el-row :gutter="12">
      <el-col v-for="f in schema" :key="f.key" :span="f.span || 12">
        <el-form-item :label="f.label" :required="!!f.required">
          <el-select v-if="f.type === 'select'" :model-value="model[f.key]"
                     :placeholder="f.placeholder || '请选择'" clearable
                     style="width:100%" :data-testid="'f-' + f.key"
                     @update:model-value="(v) => setField(f.key, v)">
            <el-option v-for="o in f.options || []" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>

          <el-input v-else-if="f.type === 'textarea'" :model-value="model[f.key]"
                    type="textarea" :rows="f.rows || 3"
                    :placeholder="f.placeholder || ''" :data-testid="'f-' + f.key"
                    @update:model-value="(v) => setField(f.key, v)" />

          <el-switch v-else-if="f.type === 'switch'" :model-value="model[f.key]"
                     :data-testid="'f-' + f.key"
                     @update:model-value="(v) => setField(f.key, v)" />

          <el-input v-else :model-value="model[f.key]"
                    :type="f.type === 'number' ? 'number' : 'text'"
                    :placeholder="f.placeholder || ''" :data-testid="'f-' + f.key"
                    @update:model-value="(v) => setField(f.key, v)" />
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup>
/**
 * 表单向导：用 schema 描述字段，替代原来的「JSON 文本框」。
 *
 * ⚠️ 关键设计（踩过坑）：**不要**在组件内直接写 `model[f.key]`。
 * `model` 是 prop，Vue 的 props 是只读代理，对它的属性赋值会被静默丢弃——
 * 表现为「输入框里有值、提交时却报请填写」。必须通过 emit 让父组件更新。
 *
 * 用法：
 *   <JsonForm :model="form" :schema="SCHEMA"
 *             @update:model="(m) => Object.assign(form, m)" />
 *
 * 约定：
 *  - schema 的 key 必须与后端 Cmd 字段名完全一致（不要猜，去读 DTO）
 *  - 枚举字段用 type:'select' + options，label 用中文
 *  - 长文本用 type:'textarea'，整行展示用 span:24
 */
const props = defineProps({
  schema: { type: Array, required: true },
  model: { type: Object, required: true }
})

const emit = defineEmits(['update:model'])

/** 每次变更回传一个完整新对象，父组件用 Object.assign 合并即可 */
function setField(key, value) {
  emit('update:model', { ...props.model, [key]: value })
}
</script>

<style scoped>
.json-form :deep(.el-form-item) { margin-bottom: 14px; }
</style>
