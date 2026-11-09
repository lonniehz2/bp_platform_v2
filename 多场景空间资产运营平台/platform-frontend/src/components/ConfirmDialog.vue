<script setup>
import { confirmState, closeConfirm } from '../confirm'
</script>

<template>
  <div v-if="confirmState.open" class="modal-mask" @click.self="closeConfirm(false)">
    <div class="modal" style="max-width:420px">
      <div class="panel-head"><h2>{{ confirmState.title }}</h2></div>
      <p class="muted" style="margin:8px 0 18px;line-height:1.7">{{ confirmState.message }}</p>
      <div class="row" style="justify-content:flex-end">
        <button class="sm" @click="closeConfirm(false)">{{ confirmState.cancelText }}</button>
        <button class="sm" :class="{ primary: !confirmState.danger, danger: confirmState.danger }" @click="closeConfirm(true)">{{ confirmState.confirmText }}</button>
      </div>
    </div>
  </div>
</template>
