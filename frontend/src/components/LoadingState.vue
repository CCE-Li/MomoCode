<template>
  <div class="card" role="status" aria-live="polite">
    <div class="stat-label">加载中…</div>
    <div class="skeleton-line" style="margin-top: 12px"></div>
    <div class="skeleton-line" style="margin-top: 8px; width: 72%"></div>
    <div class="skeleton-line" style="margin-top: 8px; width: 48%"></div>
  </div>
</template>

<style scoped>
.skeleton-line {
  height: 12px;
  border-radius: var(--radius-full);
  background: var(--surface-muted);
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.55;
  }
  50% {
    opacity: 1;
  }
}
</style>
