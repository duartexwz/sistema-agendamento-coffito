import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const localApiProxy = {
  target: 'http://0.0.0.1:8090',
  changeOrigin: true,
  secure: false,
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
      '/api/v1': localApiProxy,
    },
  },
});
