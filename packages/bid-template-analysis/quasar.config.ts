import { defineConfig } from '@quasar/app-vite';

export default defineConfig(() => ({
  css: ['app.scss'],
  build: {
    typescript: { strict: true, vueShim: true },
    vueRouterMode: 'hash',
  },
  devServer: {
    host: '0.0.0.0',
    port: Number(process.env.VITE_DEV_PORT || 3003),
    open: false,
  },
  framework: { config: {}, plugins: [] },
  extras: ['roboto-font', 'material-icons'],
}));
