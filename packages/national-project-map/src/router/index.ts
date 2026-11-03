import { defineRouter } from '@quasar/app-vite';
import { createRouter, createWebHashHistory } from 'vue-router';

export default defineRouter(() =>
  createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/', component: () => import('../pages/index.vue') },
      { path: '/projects/:projectId', component: () => import('../pages/project-detail.vue') },
      { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
  }),
);
