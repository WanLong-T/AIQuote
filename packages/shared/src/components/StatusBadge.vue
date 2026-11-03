<template>
  <span class="status-badge" :class="`status-badge--${tone}`"><slot /></span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: 'info' | 'success' | 'warning' | 'danger' | 'muted';
  }>(),
  { tone: 'info' },
);
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border: 1px solid currentcolor;
  border-radius: 999px;
  font-size: 12px;
  line-height: 1;
}

.status-badge--info { color: #55c9ff; }
.status-badge--success { color: #47dfb1; }
.status-badge--warning { color: #ffbd62; }
.status-badge--danger { color: #ff7894; }
.status-badge--muted { color: #83a2bf; }
</style>
