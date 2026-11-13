<script setup lang="ts">
const props = defineProps<{
  message: string
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="empty-state" role="alert">
    <h2>加载失败</h2>
    <p>{{ props.message }}</p>
    <button class="btn btn-ghost" type="button" @click="emit('retry')">重试</button>
  </div>
</template>
