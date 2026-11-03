<template>
  <main class="module-page">
    <div class="module-page__content">
      <p class="eyebrow">ANALYSIS DETAIL ROUTE</p>
      <h1>模板分析详情占位页</h1>
      <p>分析编号：{{ analysisId }}</p>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
const rawAnalysisId = (route.params as Record<string, string | string[]>).analysisId;
const analysisId = Array.isArray(rawAnalysisId) ? rawAnalysisId[0] ?? '' : rawAnalysisId ?? '';
</script>

<style scoped>
.eyebrow { color: #4fcfff; font-size: 12px; letter-spacing: .14em; }
h1 { margin: 0; font-size: 34px; }
p:last-child { color: #8faccc; }
</style>
