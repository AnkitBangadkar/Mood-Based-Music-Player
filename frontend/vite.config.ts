import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/generate': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/scan': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/library': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/songs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/audio': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/lyrics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})