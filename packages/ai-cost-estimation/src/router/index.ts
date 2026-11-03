import { defineRouter } from '@quasar/app-vite';
import { createRouter, createWebHashHistory } from 'vue-router';

export default defineRouter(() =>
  createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', component: () => import('../pages/index.vue') },
      { path: '/estimates', component: () => import('../pages/index.vue') },
      { path: '/estimates/:estimateId', component: () => import('../pages/estimate-detail.vue') },
      { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
  }),
);
