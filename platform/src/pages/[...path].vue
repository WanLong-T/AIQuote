<template>
  <q-page class="not-found-page">
    <div class="not-found-card tech-panel">
      <div class="error-code">404</div>
      <h1>未找到该页面</h1>
      <p>你访问的地址不存在或已被移动。</p>
      <q-btn to="/" unelevated icon="home" label="返回项目地图" class="home-button" no-caps />
    </div>
  </q-page>
</template>

<style scoped lang="scss">
.not-found-page {
  display: grid;
  min-height: calc(100vh - 74px);
  padding: 30px;
  place-items: center;
}
.not-found-card {
  width: min(520px, 100%);
  padding: 58px 35px;
  text-align: center;
}
.error-code {
  color: transparent;
  background: linear-gradient(180deg, #78e6ff, #1479ee);
  background-clip: text;
  font-size: clamp(76px, 12vw, 128px);
  font-weight: 700;
  line-height: 1;
  letter-spacing: 7px;
  filter: drop-shadow(0 0 20px rgb(36 158 255 / 25%));
}
h1 {
  margin: 22px 0 8px;
  color: #eff9ff;
  font-size: 22px;
  font-weight: 600;
}
p {
  margin: 0 0 27px;
  color: #6f94b8;
}
.home-button {
  color: #fff;
  background: linear-gradient(180deg, #168fea, #0d5fbd);
  border: 1px solid rgb(71 194 255 / 48%);
}
</style>
