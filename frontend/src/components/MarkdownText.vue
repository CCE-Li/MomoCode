<script setup lang="ts">
defineProps<{
  content: string
}>()
</script>

<template>
  <div class="markdown-text">{{ content }}</div>
</template>

<style scoped>
.markdown-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: var(--text);
  line-height: 1.7;
}
</style>
