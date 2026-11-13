import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      {
        find: '@',
        replacement: fileURLToPath(new URL('./src', import.meta.url)),
      },
      {
        find: /^monaco-editor\/esm\/vs\/editor\/editor\.api$/,
        replacement: fileURLToPath(
          new URL(
            './node_modules/monaco-editor/esm/vs/editor/editor.api.js',
            import.meta.url,
          ),
        ),
      },
      {
        find: /^monaco-editor\/esm\/vs\/editor\/common\/commands\/shiftCommand$/,
        replacement: fileURLToPath(
          new URL(
            './node_modules/monaco-editor/esm/vs/editor/common/commands/shiftCommand.js',
            import.meta.url,
          ),
        ),
      },
    ],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
