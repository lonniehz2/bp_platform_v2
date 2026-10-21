<template>
  <el-form :model="model" label-width="110px" size="default" class="json-form">
    <el-row :gutter="12">
      <el-col v-for="f in schema" :key="f.key" :span="f.span || 12">
        <el-form-item :label="f.label" :required="!!f.required">
          <el-select v-if="f.type === 'select'" v-model="model[f.key]"
                     :placeholder="f.placeholder || '请选择'" clearable
                     style="width:100%" :data-testid="'f-' + f.key">
            <el-option v-for="o in f.options || []" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>

          <el-input v-else-if="f.type === 'textarea'" v-model="model[f.key]"
                    type="textarea" :rows="f.rows || 3"
                    :placeholder="f.placeholder || ''" :data-testid="'f-' + f.key" />

          <el-switch v-else-if="f.type === 'switch'" v-model="model[f.key]"
                     :data-testid="'f-' + f.key" />

          <el-input v-else v-model="model[f.key]" :type="f.type === 'number' ? 'number' : 'text'"
                    :placeholder="f.placeholder || ''" :data-testid="'f-' + f.key" />
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup>
/**
 * 表单向导：用 schema 描述字段，替代原来的「JSON 文本框」。
 *
 * 为什么做这个组件：此前 8 个页面让用户直接粘 JSON 提交，示例里还缺必填字段，
 * 照抄必然 400。改成受控表单后，必填项、枚举值都从 schema 来，手滑也提交不了脏数据。
 *
 * 约定：
 *  - schema 的 key 必须与后端 Cmd 的字段名完全一致（不要猜，去读 DTO）
 *  - 枚举字段用 type:'select' + options，label 用中文
 *  - 长文本用 type:'textarea'，整行展示用 span:24
 */
defineProps({
  schema: { type: Array, required: true },
  model: { type: Object, required: true }
})
</script>

<style scoped>
.json-form :deep(.el-form-item) { margin-bottom: 14px; }
</style>
