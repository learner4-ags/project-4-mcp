import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/ui', timeout: 20000, fullyParallel: false, reporter: [['list']],
  use: { baseURL: process.env.BASE_URL || 'http://127.0.0.1:8000' },
  webServer: process.env.BASE_URL ? undefined : {
    command: 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
    url: 'http://127.0.0.1:8000/health', reuseExistingServer: true, timeout: 20000,
  },
});
