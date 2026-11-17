import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// SUPR_API_URL lets end-to-end tests point the dev server at an isolated backend.
const api = process.env.SUPR_API_URL || 'http://127.0.0.1:8000';
export default defineConfig({plugins:[react()],server:{proxy:{'/api':api}}});
