<template>
  <main class="module-page">
    <div class="module-page__content">
      <p class="eyebrow">ESTIMATE DETAIL ROUTE</p>
      <h1>成本测算详情占位页</h1>
      <p>测算编号：{{ estimateId }}</p>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
const rawEstimateId = (route.params as Record<string, string | string[]>).estimateId;
const estimateId = Array.isArray(rawEstimateId) ? rawEstimateId[0] ?? '' : rawEstimateId ?? '';
</script>

<style scoped>
.eyebrow { color: #4fcfff; font-size: 12px; letter-spacing: .14em; }
h1 { margin: 0; font-size: 34px; }
p:last-child { color: #8faccc; }
</style>
