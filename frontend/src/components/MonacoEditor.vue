<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as monaco from 'monaco-editor/editor/editor.api'
import 'monaco-editor/languages/definitions/cpp/register'
import 'monaco-editor/editor/contrib/linesOperations/browser/linesOperations'
import type * as Monaco from 'monaco-editor'
import { initVimMode, VimMode, type VimAdapterInstance } from 'monaco-vim'

const props = withDefaults(
  defineProps<{
    modelValue: string
    language?: string
    theme?: 'vs' | 'vs-dark'
    readOnly?: boolean
    vimEnabled?: boolean
  }>(),
  {
    language: 'cpp',
    theme: 'vs-dark',
    readOnly: false,
    vimEnabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const container = ref<HTMLElement | null>(null)
const vimStatus = ref<HTMLElement | null>(null)
let editor: Monaco.editor.IStandaloneCodeEditor | null = null
let contentSubscription: Monaco.IDisposable | null = null
let vimMode: VimAdapterInstance | null = null
let vimNewlinePatched = false

function installVimNewlineFix(): void {
  if (vimNewlinePatched) return

  const vim = VimMode as unknown as {
    commands: { newlineAndIndent: (adapter: unknown) => void }
  }
  vim.commands.newlineAndIndent = (adapter: unknown) => {
    const cm = adapter as {
      editor?: Monaco.editor.IStandaloneCodeEditor
    }
    const current = cm.editor
    const model = current?.getModel()
    const position = current?.getPosition()
    if (!current || !model || !position || current.getOption(monaco.editor.EditorOption.readOnly)) {
      return
    }

    const line = model.getLineContent(position.lineNumber)
    const indent = line.match(/^\s*/)?.[0] ?? ''
    const column = model.getLineMaxColumn(position.lineNumber)
    current.executeEdits('vim-newline', [
      {
        range: new monaco.Range(position.lineNumber, column, position.lineNumber, column),
        text: `\n${indent}`,
        forceMoveMarkers: true,
      },
    ])
    current.setPosition({
      lineNumber: position.lineNumber + 1,
      column: indent.length + 1,
    })
    current.focus()
  }
  vimNewlinePatched = true
}

function enableVim(): void {
  if (!editor || !vimStatus.value || vimMode) return
  installVimNewlineFix()
  vimMode = initVimMode(editor, vimStatus.value)
}

function disableVim(): void {
  vimMode?.dispose()
  vimMode = null
  if (vimStatus.value) {
    vimStatus.value.textContent = ''
  }
}

onMounted(() => {
  if (!container.value) return

  monaco.editor.setTheme(props.theme)
  editor = monaco.editor.create(container.value, {
    value: props.modelValue,
    language: props.language,
    theme: props.theme,
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 14,
    lineHeight: 22,
    scrollBeyondLastLine: false,
    readOnly: props.readOnly,
    accessibilitySupport: 'auto',
    padding: { top: 12, bottom: 12 },
    tabSize: 4,
  })

  contentSubscription = editor.onDidChangeModelContent(() => {
    emit('update:modelValue', editor?.getValue() ?? '')
  })

  if (props.vimEnabled) {
    nextTick(enableVim)
  }
})

watch(
  () => props.modelValue,
  (value) => {
    if (editor && editor.getValue() !== value) {
      editor.setValue(value)
    }
  },
)

watch(
  () => props.readOnly,
  (value) => {
    editor?.updateOptions({ readOnly: value })
  },
)

watch(
  () => props.theme,
  (value) => {
    monaco.editor.setTheme(value)
  },
)

watch(
  () => props.vimEnabled,
  (value) => {
    if (value) {
      nextTick(enableVim)
    } else {
      disableVim()
    }
  },
)

onBeforeUnmount(() => {
  disableVim()
  contentSubscription?.dispose()
  editor?.dispose()
  editor = null
})
</script>

<template>
  <div class="monaco-shell">
    <div ref="container" class="monaco-host" aria-label="代码编辑器" />
    <div v-show="vimEnabled" ref="vimStatus" class="vim-status" aria-live="polite" />
  </div>
</template>

<style scoped>
.monaco-shell {
  height: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.monaco-host {
  height: 100%;
  min-height: 0;
}

.vim-status {
  min-height: 26px;
  padding: 4px 12px;
  border-top: 1px solid var(--border);
  background: var(--surface-muted);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 18px;
}

.vim-status :deep(input) {
  min-height: 22px;
  padding: 0 4px;
  border: 1px solid var(--border-strong);
  border-radius: 2px;
  background: var(--surface);
  color: var(--text);
  font-family: var(--font-mono);
}

.vim-status :deep(.vim-notification) {
  color: var(--accent);
}
</style>
