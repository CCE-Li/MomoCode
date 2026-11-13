<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'

const route = useRoute()

const pageTitle = computed(() => {
  const title = route.meta.title
  return typeof title === 'string' ? title : '训练'
})
</script>

<template>
  <div class="focus-shell">
    <header class="focus-topbar">
      <div class="topbar-actions">
        <RouterLink class="btn btn-ghost" to="/">返回仪表盘</RouterLink>
        <span class="topbar-title">{{ pageTitle }}</span>
      </div>
      <div class="topbar-actions">
        <ThemeToggle />
      </div>
    </header>

    <main class="focus-content">
      <RouterView />
    </main>
  </div>
</template>
