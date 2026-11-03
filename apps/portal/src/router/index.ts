import { defineRouter } from '@quasar/app-vite';
import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router';
import { portalModules } from '../config/modules';

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/map' },
  ...portalModules.map((module) => ({
    path: module.route,
    component: () => import('../pages/index.vue'),
  })),
  { path: '/:pathMatch(.*)*', redirect: '/map' },
];

export default defineRouter(() =>
  createRouter({
    history: createWebHashHistory(),
    routes,
    scrollBehavior: () => ({ left: 0, top: 0 }),
  }),
);
