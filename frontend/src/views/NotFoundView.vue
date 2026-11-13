<script setup lang="ts">
import { RouterLink } from 'vue-router'
import EmptyState from '@/components/EmptyState.vue'
</script>

<template>
  <main class="auth-shell">
    <EmptyState
      title="页面不存在"
      description="链接可能已失效，或资源不属于当前账号。"
    >
      <RouterLink class="btn btn-primary" to="/">返回仪表盘</RouterLink>
    </EmptyState>
  </main>
</template>
