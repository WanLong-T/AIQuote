<template>
  <ModuleFrame v-if="module" :module="module" />
</template>

<script setup lang="ts">
import ModuleFrame from '../components/ModuleFrame.vue';
import { portalModules, type PortalModule } from '../config/modules';

const props = defineProps<{ moduleKey: PortalModule['key'] }>();
const module = portalModules.find((item) => item.key === props.moduleKey);
</script>
