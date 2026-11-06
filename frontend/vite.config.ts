/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    // Dựng jsdom + import React/Router cho 30 file song song chiếm ~70% thời gian;
    // test đầu tiên mỗi file mất 1–3 giây, máy bận thì vượt mặc định 5 giây
    testTimeout: 15000,
    hookTimeout: 15000,
  },
})
