<template>
  <main class="module-frame">
    <header class="module-frame__header">
      <div>
        <h1>{{ module.label }}</h1>
        <p>{{ module.description }}</p>
      </div>
      <RouterLink to="/map" class="module-frame__back">返回项目地图</RouterLink>
    </header>
    <iframe :src="entryUrl" :title="module.label" class="module-frame__iframe" />
  </main>
</template>

<script setup lang="ts">
import type { PortalModule } from '../config/modules';
import { moduleEntryUrl } from '../config/modules';

const props = defineProps<{ module: PortalModule }>();
const entryUrl = moduleEntryUrl(props.module);
</script>

<style scoped>
.module-frame { display: grid; min-height: 100vh; padding: 20px; gap: 16px; color: #f4fbff; background: #03132f; }
.module-frame__header { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
h1 { margin: 0; font-size: 24px; }
.module-frame__header p:last-child { margin: 6px 0 0; color: #8faccc; }
.module-frame__back { color: #4fcfff; }
.module-frame__iframe { width: 100%; min-height: calc(100vh - 115px); border: 1px solid rgb(76 165 231 / 22%); background: #03132f; }
</style>
