import { defineRouter } from '@quasar/app-vite';
import { createRouter, createWebHashHistory } from 'vue-router';

export default defineRouter(() =>
  createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', component: () => import('../pages/index.vue') },
      { path: '/results', component: () => import('../pages/index.vue') },
      { path: '/results/:resultId', component: () => import('../pages/result-detail.vue') },
      { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
  }),
);
