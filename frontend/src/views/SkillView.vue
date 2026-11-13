<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import TaskCard from '@/components/TaskCard.vue'
import { catalogApi } from '@/api/catalog'
import { practiceApi } from '@/api/practice'
import { getApiErrorMessage } from '@/api/client'
import type { SkillDetail, TaskSummary } from '@/types/catalog'

const route = useRoute()
const router = useRouter()
const skillSlug = computed(() => String(route.params.skillSlug ?? ''))
const skill = ref<SkillDetail | null>(null)
const tasks = ref<TaskSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const startingTaskId = ref<string | null>(null)
const startError = ref<string | null>(null)

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
    const [skillData, taskData] = await Promise.all([
      catalogApi.skill(skillSlug.value),
      catalogApi.tasks({ skill: skillSlug.value }),
    ])
    skill.value = skillData
    tasks.value = taskData
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function startTask(task: TaskSummary): Promise<void> {
  startingTaskId.value = task.id
  startError.value = null
  try {
    const session = await practiceApi.createSession(task.id, 'free')
    await router.push(`/practice/sessions/${session.id}`)
  } catch (err) {
    startError.value = getApiErrorMessage(err)
  } finally {
    startingTaskId.value = null
  }
}

onMounted(load)
watch(skillSlug, load)
</script>

<template>
  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <template v-else-if="skill">
    <PageHeader :title="skill.name" :description="skill.learning_objective ?? undefined">
      <template #actions>
        <RouterLink
          class="btn btn-ghost"
          :to="`/library/algorithms/${skill.algorithm_slug}`"
        >
          返回 {{ skill.algorithm_name }}
        </RouterLink>
      </template>
    </PageHeader>

    <div class="topbar-actions" style="margin-bottom: 16px">
      <span class="badge badge-accent">
        {{ typeLabels[skill.skill_type] ?? skill.skill_type }}
      </span>
      <span class="badge">{{ skill.algorithm_name }}</span>
    </div>

    <div class="grid grid-2" style="margin-bottom: 16px">
      <section class="card">
        <h2>学习目标</h2>
        <p style="color: var(--text-muted); margin-top: 8px">
          {{ skill.description_md ?? '暂无描述' }}
        </p>
        <p style="color: var(--text-muted); margin-top: 8px">
          {{ skill.learning_objective ?? '' }}
        </p>
      </section>
      <section class="card">
        <h2>掌握证据</h2>
        <p style="color: var(--text-muted); margin-top: 8px">
          {{ skill.mastery_evidence_md ?? '暂无说明' }}
        </p>
      </section>
      <section class="card">
        <h2>前置知识</h2>
        <div v-if="skill.prerequisites.length" class="topbar-actions" style="margin-top: 8px">
          <span v-for="item in skill.prerequisites" :key="item" class="badge">
            {{ item }}
          </span>
        </div>
        <p v-else style="color: var(--text-muted); margin-top: 8px">无</p>
      </section>
      <section class="card">
        <h2>常见错误</h2>
        <p style="color: var(--text-muted); margin-top: 8px; white-space: pre-wrap">
          {{ skill.common_mistakes_md ?? '暂无说明' }}
        </p>
      </section>
    </div>

    <section class="card">
      <h2>训练任务</h2>
      <div
        v-if="startError"
        class="notice"
        role="alert"
        style="border-color: var(--danger); color: var(--danger); margin-top: 12px"
      >
        {{ startError }}
      </div>
      <div v-if="tasks.length" class="grid grid-2" style="margin-top: 16px">
        <TaskCard
          v-for="task in tasks"
          :key="task.id"
          :task="task"
          :action-label="startingTaskId === task.id ? '创建中…' : '开始练习'"
          @start="startTask"
        />
      </div>
      <EmptyState
        v-else
        title="该技能暂无训练任务"
        description="内容团队可在后续版本补充任务。"
      />
    </section>
  </template>
</template>
