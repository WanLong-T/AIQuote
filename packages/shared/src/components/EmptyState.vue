<template>
  <section class="empty-state">
    <strong>{{ title }}</strong>
    <p v-if="description">{{ description }}</p>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string;
    description?: string;
  }>(),
  { description: '' },
);
</script>

<style scoped>
.empty-state {
  display: grid;
  min-height: 180px;
  padding: 24px;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #83a2bf;
  text-align: center;
  border: 1px dashed rgb(81 171 230 / 30%);
  border-radius: 8px;
}

strong { color: #d9efff; }
p { margin: 0; }
</style>
