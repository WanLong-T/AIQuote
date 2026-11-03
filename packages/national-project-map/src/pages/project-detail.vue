<template>
  <main class="module-page">
    <div class="module-page__content">
      <p class="eyebrow">PROJECT DETAIL ROUTE</p>
      <h1>项目详情占位页</h1>
      <p>项目编号：{{ projectId }}</p>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
const rawProjectId = (route.params as Record<string, string | string[]>).projectId;
const projectId = Array.isArray(rawProjectId) ? rawProjectId[0] ?? '' : rawProjectId ?? '';
</script>

<style scoped>
.eyebrow { color: #4fcfff; font-size: 12px; letter-spacing: .14em; }
h1 { margin: 0; font-size: 34px; }
p:last-child { color: #8faccc; }
</style>
