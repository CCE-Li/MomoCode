<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import { catalogApi } from '@/api/catalog'
import { getApiErrorMessage } from '@/api/client'
import type { AlgorithmDetail } from '@/types/catalog'

const route = useRoute()
const algorithmSlug = computed(() => String(route.params.algorithmSlug ?? ''))
const algorithm = ref<AlgorithmDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const typeLabels: Record<string, string> = {
  recognition: '识别',
  base_implementation: '基础实现',
  variant: '变体',
  common_error: '常见错误',
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    algorithm.value = await catalogApi.algorithm(algorithmSlug.value)
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(algorithmSlug, load)
</script>

<template>
  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <template v-else-if="algorithm">
    <PageHeader :title="algorithm.name" :description="algorithm.summary ?? undefined">
      <template #actions>
        <RouterLink class="btn btn-ghost" to="/library">返回算法库</RouterLink>
      </template>
    </PageHeader>

    <div class="topbar-actions" style="margin-bottom: 16px">
      <span class="badge badge-accent">{{ algorithm.category_name }}</span>
      <span class="badge">难度 {{ algorithm.difficulty }}</span>
      <span class="badge">{{ algorithm.skill_count }} 个技能</span>
    </div>

    <section v-if="algorithm.description_md" class="card" style="margin-bottom: 16px">
      <h2>概览</h2>
      <p style="white-space: pre-wrap; margin-top: 8px; color: var(--text-muted)">
        {{ algorithm.description_md }}
      </p>
    </section>

    <section class="card">
      <h2>技能</h2>
      <div v-if="algorithm.skills.length" class="grid grid-2" style="margin-top: 16px">
        <article v-for="skill in algorithm.skills" :key="skill.id" class="card card-muted">
          <div class="topbar-actions" style="justify-content: space-between">
            <h3>{{ skill.name }}</h3>
            <span class="badge">{{ typeLabels[skill.skill_type] ?? skill.skill_type }}</span>
          </div>
          <p v-if="skill.learning_objective" style="color: var(--text-muted); margin-top: 8px">
            {{ skill.learning_objective }}
          </p>
          <RouterLink
            class="btn btn-ghost"
            :to="`/library/skills/${skill.slug}`"
            style="margin-top: 12px"
          >
            查看技能
          </RouterLink>
        </article>
      </div>
      <EmptyState v-else title="技能内容准备中" />
    </section>
  </template>
</template>
