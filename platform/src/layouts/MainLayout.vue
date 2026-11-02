<template>
  <q-layout view="hHh Lpr lFf" class="app-layout">
    <q-header class="app-header">
      <q-toolbar class="header-toolbar">
        <q-btn
          class="mobile-menu lt-md"
          flat
          dense
          round
          icon="menu"
          aria-label="打开导航菜单"
          @click="drawerOpen = !drawerOpen"
        />

        <div class="brand">
          <div class="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <div>
            <div class="brand-title">工程投标智能决策系统</div>
            <div class="brand-subtitle">INTELLIGENT BIDDING DECISION SYSTEM</div>
          </div>
        </div>

        <q-space />

        <div class="system-state gt-sm">
          <span class="state-dot" />
          <span>系统运行正常</span>
        </div>
        <div class="header-divider gt-sm" />

        <div class="header-actions">
          <q-btn flat round icon="search" aria-label="搜索" />
          <q-btn flat round icon="notifications_none" aria-label="消息通知">
            <q-badge color="red-5" floating rounded>3</q-badge>
          </q-btn>
          <q-btn class="gt-xs" flat round icon="settings" aria-label="系统设置" />
        </div>

        <div class="header-divider gt-xs" />

        <div class="user-panel gt-xs">
          <q-avatar size="36px" class="user-avatar">
            <q-icon name="person" size="21px" />
          </q-avatar>
          <div class="gt-sm">
            <div class="user-name">系统管理员</div>
            <div class="user-role">决策中心</div>
          </div>
          <q-icon class="gt-sm" name="keyboard_arrow_down" size="18px" />
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawerOpen" show-if-above :width="250" :breakpoint="1024" class="app-drawer">
      <div class="drawer-content">
        <div class="nav-caption">
          <span>核心功能</span>
          <span class="nav-caption__line" />
        </div>

        <q-list class="nav-list">
          <q-item
            v-for="item in navigation"
            :key="item.path"
            v-ripple
            clickable
            :to="item.path"
            :exact="item.path === '/'"
            class="nav-item"
            active-class="nav-item--active"
          >
            <q-item-section avatar>
              <span class="nav-icon"><q-icon :name="item.icon" size="21px" /></span>
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption>{{ item.caption }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon name="chevron_right" size="17px" />
            </q-item-section>
          </q-item>
        </q-list>

        <div class="drawer-spacer" />

        <button class="data-card" type="button" @click="showDataCenter = true">
          <div class="data-card__icon"><q-icon name="storage" size="19px" /></div>
          <div>
            <div class="data-card__title">数据中心</div>
            <div class="data-card__status" :class="{ 'data-card__status--error': !dataCenter.connected }">
              <span /> {{ dataCenter.connected ? 'MySQL 连接正常' : '数据库连接异常' }}
            </div>
          </div>
          <q-icon class="data-card__arrow" name="chevron_right" size="17px" />
        </button>

        <div class="drawer-footer">VERSION 1.0.0 · DECISION PLATFORM</div>
      </div>
    </q-drawer>

    <q-dialog v-model="showDataCenter">
      <q-card class="data-center-dialog">
        <q-card-section class="data-center-dialog__header">
          <div>
            <div class="data-center-dialog__eyebrow">DATA CENTER</div>
            <div class="data-center-dialog__title">MySQL 数据中心</div>
          </div>
          <q-btn v-close-popup flat round icon="close" aria-label="关闭" />
        </q-card-section>
        <q-card-section class="data-center-dialog__body">
          <div class="database-state" :class="{ 'database-state--error': !dataCenter.connected }">
            <q-icon :name="dataCenter.connected ? 'check_circle' : 'error'" size="25px" />
            <div>
              <strong>{{ dataCenter.connected ? '数据库连接正常' : '数据库暂时不可用' }}</strong>
              <span>前端数据通过本机 9000 端口实时读取 MySQL</span>
            </div>
          </div>
          <div class="data-center-grid">
            <div><span>数据库</span><strong>{{ dataCenter.database || '—' }}</strong></div>
            <div><span>数据表</span><strong>{{ dataCenter.table || '—' }}</strong></div>
            <div><span>项目总数</span><strong>{{ dataCenter.projectCount }}</strong></div>
            <div><span>有效招标项目</span><strong>{{ dataCenter.opportunityCount }}</strong></div>
          </div>
          <div class="data-center-time">
            <q-icon name="schedule" /> 最近入库更新：{{ formatDataTime(dataCenter.updatedAt) }}
          </div>
        </q-card-section>
        <q-card-actions class="data-center-actions" align="right">
          <q-btn
            outline
            color="light-blue-4"
            icon="data_object"
            label="下载 JSON"
            :disable="!dataCenter.connected"
            @click="downloadDatabase('json')"
          />
          <q-btn
            unelevated
            color="light-blue-7"
            icon="download"
            label="下载 CSV 数据"
            :disable="!dataCenter.connected"
            @click="downloadDatabase('csv')"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-page-container class="page-container">
      <router-view #default="{ Component, route }">
        <keep-alive :max="4">
          <component :is="Component" :key="route.name" />
        </keep-alive>
      </router-view>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

interface NavigationItem {
  label: string;
  caption: string;
  icon: string;
  path: string;
}

const drawerOpen = ref(false);
const showDataCenter = ref(false);
const dataCenter = ref({
  connected: false,
  database: '',
  table: '',
  projectCount: 0,
  opportunityCount: 0,
  updatedAt: '',
});
let statusTimer: ReturnType<typeof setInterval> | undefined;

async function loadDataCenterStatus(): Promise<void> {
  try {
    const response = await fetch(`/api/data-center/status?t=${Date.now()}`, { cache: 'no-store' });
    if (!response.ok) throw new Error('database unavailable');
    const result = (await response.json()) as Partial<typeof dataCenter.value>;
    dataCenter.value = { ...dataCenter.value, ...result, connected: true };
  } catch {
    dataCenter.value.connected = false;
  }
}

function formatDataTime(value: string): string {
  if (!value) return '暂无记录';
  return value.replace('T', ' ').replace(/\.\d+Z?$/, '');
}

function downloadDatabase(format: 'csv' | 'json'): void {
  window.location.assign(`/api/projects/export.${format}`);
}

onMounted(() => {
  void loadDataCenterStatus();
  statusTimer = setInterval(() => void loadDataCenterStatus(), 60_000);
});

onBeforeUnmount(() => {
  if (statusTimer) clearInterval(statusTimer);
});

const navigation: NavigationItem[] = [
  { label: '全国项目地图', caption: '项目态势总览', icon: 'public', path: '/' },
  { label: 'AI 成本测算', caption: '智能成本分析', icon: 'calculate', path: '/cost' },
  { label: '投标模板分析', caption: '方案模拟评估', icon: 'description', path: '/template' },
  { label: '投标结果分析', caption: '结果复盘洞察', icon: 'insights', path: '/result' },
];
</script>

<style scoped lang="scss">
.app-layout {
  min-height: 100vh;
  color: var(--text-main);
  background: #03132f;
}

.app-header {
  color: #f7fbff;
  background: linear-gradient(100deg, #061735 0%, #082652 55%, #071c3f 100%);
  border-bottom: 1px solid rgb(63 166 255 / 28%);
  box-shadow: 0 8px 34px rgb(0 7 26 / 42%);
}

.app-header::after {
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 1px;
  content: '';
  background: linear-gradient(
    90deg,
    transparent,
    #1aa8ff 24%,
    rgb(26 168 255 / 20%) 58%,
    transparent
  );
}

.header-toolbar {
  min-height: 74px;
  padding: 0 25px;
}

.mobile-menu {
  margin-right: 10px;
  color: #73ccff;
}
.brand {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 14px;
}
.brand-mark {
  display: grid;
  width: 42px;
  height: 42px;
  padding: 9px 8px;
  align-content: center;
  gap: 4px;
  background: linear-gradient(145deg, rgb(21 134 255 / 35%), rgb(4 55 116 / 42%));
  border: 1px solid rgb(77 191 255 / 43%);
  border-radius: 6px;
  box-shadow:
    inset 0 0 20px rgb(40 165 255 / 13%),
    0 0 20px rgb(24 133 255 / 13%);
}
.brand-mark span {
  display: block;
  height: 3px;
  background: linear-gradient(90deg, #2d89ff, #48d8ff);
  border-radius: 3px;
  box-shadow: 0 0 8px #159bff;
}
.brand-mark span:nth-child(2) {
  width: 72%;
}
.brand-mark span:nth-child(3) {
  width: 44%;
}
.brand-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1.4px;
  white-space: nowrap;
}
.brand-subtitle {
  margin-top: 3px;
  color: #668db8;
  font-size: 10px;
  letter-spacing: 1.75px;
  white-space: nowrap;
}
.system-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8faccc;
  font-size: 12px;
}
.state-dot {
  width: 6px;
  height: 6px;
  background: #2ce3ad;
  border-radius: 50%;
  box-shadow:
    0 0 0 4px rgb(44 227 173 / 10%),
    0 0 11px #2ce3ad;
}
.header-divider {
  width: 1px;
  height: 28px;
  margin: 0 14px;
  background: rgb(124 174 221 / 16%);
}
.header-actions {
  display: flex;
  color: #7ea9d1;
  gap: 2px;
}
.header-actions :deep(.q-btn) {
  transition: 180ms ease;
}
.header-actions :deep(.q-btn:hover) {
  color: #64d2ff;
  background: rgb(37 135 218 / 15%);
}
.user-panel {
  display: flex;
  align-items: center;
  gap: 9px;
}
.user-avatar {
  color: #a7e8ff;
  background: linear-gradient(145deg, #174f89, #0c315f);
  border: 1px solid rgb(98 196 255 / 31%);
}
.user-name {
  color: #eaf6ff;
  font-size: 13px;
  font-weight: 500;
}
.user-role {
  margin-top: 2px;
  color: #6386a9;
  font-size: 11px;
}

.app-drawer {
  color: #bdd5ec;
  background: linear-gradient(180deg, #061735 0%, #072655 56%, #041936 100%);
  border-right: 1px solid rgb(61 150 229 / 22%);
}
:deep(.app-drawer .q-drawer__content) {
  overflow: hidden;
}
.drawer-content {
  display: flex;
  height: 100%;
  padding: 25px 13px 16px;
  flex-direction: column;
}
.nav-caption {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px 16px;
  color: #7ea4c9;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 1.2px;
}
.nav-caption__line {
  width: 25px;
  height: 2px;
  background: #168cff;
  box-shadow: 0 0 8px #168cff;
}
.nav-list {
  display: grid;
  gap: 9px;
}
.nav-item {
  min-height: 68px;
  color: #89a9c9;
  border: 1px solid transparent;
  border-radius: 6px;
  transition: 180ms ease;
}
.nav-item:hover {
  color: #dff5ff;
  background: rgb(24 105 188 / 15%);
  border-color: rgb(76 163 237 / 12%);
}
.nav-item :deep(.q-item__section--avatar) {
  min-width: 46px;
}
.nav-icon {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #438ecf;
  border: 1px solid rgb(75 151 220 / 19%);
  border-radius: 5px;
  background: rgb(17 75 137 / 18%);
}
.nav-item :deep(.q-item__label:not(.q-item__label--caption)) {
  color: inherit;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.nav-item :deep(.q-item__label--caption) {
  margin-top: 5px;
  color: #6f99c0;
  font-size: 12px;
}
.nav-item :deep(.q-item__section--side) {
  color: #3e6b96;
}
.nav-item--active {
  color: #f4fbff;
  background: linear-gradient(90deg, rgb(15 129 249 / 65%), rgb(16 89 181 / 27%));
  border-color: rgb(58 171 255 / 37%);
  box-shadow:
    inset 3px 0 #24c4ff,
    0 0 24px rgb(8 100 220 / 17%);
}
.nav-item--active .nav-icon {
  color: #92e9ff;
  background: rgb(38 147 255 / 24%);
  border-color: rgb(83 208 255 / 30%);
  box-shadow: 0 0 16px rgb(35 164 255 / 14%);
}
.nav-item--active :deep(.q-item__label--caption) {
  color: #82b9e9;
}
.nav-item--active :deep(.q-item__section--side) {
  color: #67ceff;
}
.drawer-spacer {
  flex: 1;
}
.data-card {
  width: calc(100% - 8px);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 11px;
  margin: 0 4px 17px;
  padding: 14px;
  background: linear-gradient(135deg, rgb(11 72 139 / 38%), rgb(5 40 82 / 43%));
  border: 1px solid rgb(73 160 229 / 19%);
  border-radius: 6px;
}
.data-card:hover {
  border-color: rgb(75 196 255 / 42%);
  box-shadow: 0 0 22px rgb(17 128 225 / 16%);
}
.data-card__arrow {
  margin-left: auto;
  color: #4ba9df;
}
.data-card__icon {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #4fcfff;
  background: rgb(32 147 220 / 13%);
  border: 1px solid rgb(57 174 239 / 18%);
  border-radius: 5px;
}
.data-card__title {
  color: #bad7ee;
  font-size: 13px;
}
.data-card__status {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 5px;
  color: #7097bb;
  font-size: 11px;
}
.data-card__status span {
  width: 5px;
  height: 5px;
  background: #29dfae;
  border-radius: 50%;
  box-shadow: 0 0 7px #29dfae;
}
.data-card__status--error {
  color: #ff92a8;
}
.data-card__status--error span {
  background: #ff5476;
  box-shadow: 0 0 7px #ff5476;
}
.data-center-dialog {
  width: min(560px, 92vw);
  color: #d9edff;
  background: linear-gradient(145deg, #092a59, #061a39);
  border: 1px solid rgb(64 176 255 / 36%);
  border-radius: 10px;
  box-shadow: 0 22px 70px rgb(0 6 20 / 70%);
}
.data-center-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgb(76 165 231 / 22%);
}
.data-center-dialog__eyebrow {
  color: #35cfff;
  font-size: 11px;
  letter-spacing: 2px;
}
.data-center-dialog__title {
  margin-top: 4px;
  color: #fff;
  font-size: 21px;
  font-weight: 700;
}
.data-center-dialog__body {
  padding: 22px;
}
.database-state {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 15px;
  color: #31e3b0;
  background: rgb(24 192 147 / 9%);
  border: 1px solid rgb(49 227 176 / 22%);
  border-radius: 7px;
}
.database-state div {
  display: grid;
  gap: 3px;
}
.database-state strong {
  color: #eafff8;
  font-size: 15px;
}
.database-state span {
  color: #79a6c8;
  font-size: 12px;
}
.database-state--error {
  color: #ff6383;
  background: rgb(255 69 103 / 8%);
  border-color: rgb(255 84 118 / 24%);
}
.data-center-grid {
  display: grid;
  margin-top: 18px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.data-center-grid > div {
  display: grid;
  min-height: 78px;
  padding: 14px;
  align-content: center;
  gap: 6px;
  background: rgb(11 56 111 / 54%);
  border: 1px solid rgb(66 151 224 / 18%);
  border-radius: 6px;
}
.data-center-grid span {
  color: #759dbf;
  font-size: 12px;
}
.data-center-grid strong {
  color: #f5fbff;
  font-size: 18px;
}
.data-center-time {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 16px;
  color: #7fa8cb;
  font-size: 12px;
}
.data-center-actions {
  padding: 0 22px 22px;
  gap: 8px;
}
.data-center-actions .q-btn {
  min-height: 42px;
  padding: 0 18px;
  font-weight: 600;
}
.drawer-footer {
  color: #4d78a0;
  font-size: 10px;
  text-align: center;
  letter-spacing: 1.2px;
}

.page-container {
  min-height: 100vh;
  background:
    linear-gradient(rgb(20 93 174 / 4%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(20 93 174 / 4%) 1px, transparent 1px),
    radial-gradient(circle at 82% 8%, rgb(13 103 215 / 25%), transparent 32%),
    radial-gradient(circle at 18% 92%, rgb(0 124 194 / 12%), transparent 30%),
    linear-gradient(135deg, #03142f 0%, #062554 52%, #041a3b 100%);
  background-size:
    42px 42px,
    42px 42px,
    auto,
    auto,
    auto;
}

@media (max-width: 599px) {
  .header-toolbar {
    min-height: 64px;
    padding: 0 12px;
  }
  .brand-mark {
    width: 35px;
    height: 35px;
    padding: 7px;
  }
  .brand-title {
    font-size: 15px;
    letter-spacing: 0.5px;
  }
  .brand-subtitle {
    display: none;
  }
  .header-actions .q-btn:first-child {
    display: none;
  }
}
</style>
