<template>
  <header class="module-page-header">
    <div>
      <p v-if="eyebrow" class="module-page-header__eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p v-if="description" class="module-page-header__description">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="module-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
  eyebrow?: string;
}>();
</script>

<style scoped>
.module-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.module-page-header__eyebrow {
  margin: 0 0 8px;
  color: #4fcfff;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #f4fbff;
  font-size: clamp(24px, 3vw, 36px);
}

.module-page-header__description {
  margin: 10px 0 0;
  color: #8faccc;
}

.module-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
