// Development proxies use the same API origin contract as the production build.
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()], server: { proxy: {
  '/api': 'http://127.0.0.1:8000', '/docs': 'http://127.0.0.1:8000', '/llms.txt': 'http://127.0.0.1:8000', '/models.json': 'http://127.0.0.1:8000'
} } });
