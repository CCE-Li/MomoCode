<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import { catalogApi } from '@/api/catalog'
import { getApiErrorMessage } from '@/api/client'
import type { AlgorithmSummary, Category } from '@/types/catalog'

const categories = ref<Category[]>([])
const algorithms = ref<AlgorithmSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const search = ref('')
const selectedCategory = ref('')
let searchTimer: number | undefined

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [categoryData, algorithmData] = await Promise.all([
      catalogApi.categories(),
      catalogApi.algorithms({
        category: selectedCategory.value || undefined,
        search: search.value.trim() || undefined,
      }),
    ])
    categories.value = categoryData
    algorithms.value = algorithmData
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(selectedCategory, load)
watch(search, () => {
  if (searchTimer !== undefined) {
    window.clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(load, 300)
})

onBeforeUnmount(() => {
  if (searchTimer !== undefined) {
    window.clearTimeout(searchTimer)
  }
})
</script>

<template>
  <PageHeader
    title="算法库"
    description="按分类浏览算法与技能，查看目标、掌握证据与易错点。"
  >
    <template #actions>
      <RouterLink class="btn btn-ghost" to="/practice">自由练习</RouterLink>
    </template>
  </PageHeader>

  <div class="card" style="margin-bottom: 16px">
    <div class="topbar-actions" style="justify-content: space-between; flex-wrap: wrap">
      <div class="field" style="min-width: 260px; flex: 1">
        <label class="sr-only" for="library-search">搜索算法</label>
        <input
          id="library-search"
          v-model="search"
          type="search"
          placeholder="搜索算法名称或标识"
        />
      </div>
      <div class="topbar-actions" style="flex-wrap: wrap">
        <button
          class="btn"
          :class="{ 'btn-primary': selectedCategory === '' }"
          type="button"
          @click="selectedCategory = ''"
        >
          全部
        </button>
        <button
          v-for="category in categories"
          :key="category.id"
          class="btn"
          :class="{ 'btn-primary': selectedCategory === category.slug }"
          type="button"
          @click="selectedCategory = category.slug"
        >
          {{ category.name }}
        </button>
      </div>
    </div>
  </div>

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <EmptyState
    v-else-if="algorithms.length === 0"
    title="没有匹配的算法"
    description="尝试清除搜索或切换分类。"
  >
    <button class="btn btn-ghost" type="button" @click="search = ''; selectedCategory = ''">
      清除筛选
    </button>
  </EmptyState>

  <div v-else>
    <div class="library-count">共 {{ algorithms.length }} 个算法</div>
    <div class="library-grid">
      <article v-for="algorithm in algorithms" :key="algorithm.id" class="card library-card">
        <div class="library-card-head">
          <h2>{{ algorithm.name }}</h2>
          <span class="badge badge-accent">{{ algorithm.category_name }}</span>
        </div>
        <p class="library-card-summary">{{ algorithm.summary ?? '暂无摘要' }}</p>
        <div class="library-card-meta">
          <span class="badge">难度 {{ algorithm.difficulty }}</span>
          <span class="badge">{{ algorithm.skill_count }} 个技能</span>
        </div>
        <RouterLink
          class="library-card-link"
          :to="`/library/algorithms/${algorithm.slug}`"
        >
          查看技能 <span aria-hidden="true">→</span>
        </RouterLink>
      </article>
    </div>
  </div>
</template>

<style scoped>
.library-count {
  margin-bottom: 10px;
  color: var(--text-subtle);
  font-size: 10px;
  font-weight: 650;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.library-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.library-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.library-card-head h2 {
  font-size: 18px;
}

.library-card-summary {
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.library-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.library-card-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.library-card-link:hover {
  color: var(--accent);
}

.library-card-link span {
  transition: transform var(--duration-fast) var(--ease-out);
}

.library-card-link:hover span {
  transform: translateX(3px);
}
</style>
