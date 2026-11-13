import EditorWorker from 'monaco-editor/editor/editor.worker?worker'

interface MonacoEnvironment {
  getWorker: () => Worker
}

;(self as unknown as { MonacoEnvironment: MonacoEnvironment }).MonacoEnvironment = {
  getWorker: () => new EditorWorker(),
}
