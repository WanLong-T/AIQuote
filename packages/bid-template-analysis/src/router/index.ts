import { defineRouter } from '@quasar/app-vite';
import { createRouter, createWebHashHistory } from 'vue-router';

export default defineRouter(() =>
  createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', component: () => import('../pages/index.vue') },
      { path: '/analyses', component: () => import('../pages/index.vue') },
      { path: '/analyses/:analysisId', component: () => import('../pages/analysis-detail.vue') },
      { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
  }),
);
