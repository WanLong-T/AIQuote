<template>
  <main class="module-page">
    <div class="module-page__content">
      <p class="eyebrow">RESULT DETAIL ROUTE</p>
      <h1>投标结果详情占位页</h1>
      <p>结果编号：{{ resultId }}</p>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
const rawResultId = (route.params as Record<string, string | string[]>).resultId;
const resultId = Array.isArray(rawResultId) ? rawResultId[0] ?? '' : rawResultId ?? '';
</script>

<style scoped>
.eyebrow { color: #4fcfff; font-size: 12px; letter-spacing: .14em; }
h1 { margin: 0; font-size: 34px; }
p:last-child { color: #8faccc; }
</style>
