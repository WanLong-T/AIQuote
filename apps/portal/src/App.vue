<template>
  <!-- 加上这层 Layout 和 PageContainer -->
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <!-- 你原本的 router-view 放这里 -->
      <router-view />
    </q-page-container>
  </q-layout>
</template>