import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const localApiProxy = {
  target: 'http://127.0.0.1:8000',
  changeOrigin: true,
  secure: false,
  rewrite: (path) => path.replace(/^\/api-local/, ''),
};

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          calendar: [
            '@fullcalendar/react',
            '@fullcalendar/core',
            '@fullcalendar/daygrid',
            '@fullcalendar/timegrid',
            '@fullcalendar/interaction',
            '@fullcalendar/bootstrap5',
          ],
        },
      },
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api-local': localApiProxy,
    },
  },
});
