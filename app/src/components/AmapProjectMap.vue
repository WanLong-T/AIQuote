<template>
  <div class="amap-project-map">
    <div ref="container" class="amap-container" />

    <div v-if="loading" class="map-state">
      <span class="state-spinner" />
      <strong>正在加载高德 GIS 图层</strong>
      <small>初始化暗色底图、热力层与项目点位</small>
    </div>

    <div v-else-if="configurationMessage" class="map-state map-state--config">
      <q-icon name="key" size="30px" />
      <strong>高德地图尚未配置</strong>
      <small>{{ configurationMessage }}</small>
      <code>QCLI_AMAP_KEY / QCLI_AMAP_SECURITY_CODE</code>
    </div>

    <div v-else-if="errorMessage" class="map-state map-state--error">
      <q-icon name="error_outline" size="30px" />
      <strong>GIS 图层加载失败</strong>
      <small>{{ errorMessage }}</small>
    </div>

    <div v-if="ready && displayProjects.length === 0" class="gis-empty-state">
      <q-icon name="info_outline" />{{ emptyMessage }}
    </div>

    <div v-if="ready" class="gis-summary">
      <span>{{ summaryLabel }}</span><strong>{{ displayProjects.length }}</strong
      ><span>个项目 · 已解析点位 {{ preciseLocationCount }} 个</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import AMapLoader from '@amap/amap-jsapi-loader';
import type { AmapProjectPoint } from '../types/map';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

interface AMapOverlay {
  setMap(map: AMapMap | null): void;
}

interface AMapMarker extends AMapOverlay {
  on(event: 'click', callback: () => void): void;
}

interface AMapHeatMap {
  setDataSet(options: { data: { lng: number; lat: number; count: number }[]; max: number }): void;
  show(): void;
  hide(): void;
}

interface AMapMap {
  add(overlays: AMapOverlay | AMapOverlay[]): void;
  addControl(control: object): void;
  remove(overlays: AMapOverlay | AMapOverlay[]): void;
  setFitView(overlays?: AMapOverlay[], immediately?: boolean, avoid?: number[]): void;
  resize(): void;
  destroy(): void;
}

interface AMapNamespace {
  plugin(names: string | string[], callback: () => void): void;
  Map: new (
    container: HTMLElement,
    options: {
      center: [number, number];
      zoom: number;
      mapStyle: string;
      viewMode: '2D' | '3D';
      pitch: number;
      features: string[];
    },
  ) => AMapMap;
  Marker: new (options: {
    position: [number, number];
    content: HTMLElement;
    offset: { x: number; y: number };
    title: string;
    zIndex: number;
  }) => AMapMarker;
  Pixel: new (x: number, y: number) => { x: number; y: number };
  Scale: new (options: { position: string }) => object;
  ToolBar: new (options: {
    position: { top: string; right: string };
    liteStyle: boolean;
  }) => object;
  HeatMap: new (
    map: AMapMap,
    options: {
      radius: number;
      opacity: [number, number];
      gradient: Record<number, string>;
    },
  ) => AMapHeatMap;
  Geocoder: new (options: { city?: string }) => {
    getLocation(
      address: string,
      callback: (
        status: string,
        result: {
          geocodes?: Array<{
            location?: { getLng(): number; getLat(): number };
            level?: string;
          }>;
        },
      ) => void,
    ): void;
  };
  PlaceSearch: new (options: { city?: string; citylimit?: boolean; pageSize?: number }) => {
    search(
      keyword: string,
      callback: (
        status: string,
        result: { poiList?: { pois?: Array<{ location?: { getLng(): number; getLat(): number } }> } },
      ) => void,
    ): void;
  };
}

declare global {
  interface Window {
    _AMapSecurityConfig?: { securityJsCode?: string };
  }
}

type DisplayMode = 'count' | 'tracking' | 'rating';
const props = defineProps<{ projects: AmapProjectPoint[]; displayMode: DisplayMode }>();
const emit = defineEmits<{ projectClick: [project: AmapProjectPoint] }>();

const container = ref<HTMLDivElement | null>(null);
const loading = ref(false);
const ready = ref(false);
const errorMessage = ref('');
const displayProjects = computed(() =>
  props.displayMode === 'tracking'
    ? props.projects.filter((project) => Boolean(project.status) && project.status !== '线索阶段')
    : props.projects,
);
const resolvedLocations = ref<Record<number, { lng: number; lat: number; precise: boolean }>>({});
const locatedProjects = computed(() =>
  displayProjects.value.map((project) => ({
    ...project,
    ...(resolvedLocations.value[project.id] ?? {}),
  })),
);
const preciseLocationCount = computed(
  () => locatedProjects.value.filter((project) => project.precise).length,
);
const summaryLabel = computed(() =>
  props.displayMode === 'count' ? '热力统计' : props.displayMode === 'tracking' ? '已跟踪' : '评级点位',
);
const emptyMessage = computed(() =>
  props.displayMode === 'tracking' ? '当前筛选项目尚未录入跟踪阶段' : '当前筛选条件下暂无项目',
);

const amapKey = import.meta.env.QCLI_AMAP_KEY?.trim() ?? '';
const securityCode = import.meta.env.QCLI_AMAP_SECURITY_CODE?.trim() ?? '';
const configurationMessage = computed(() =>
  amapKey ? '' : '请在项目根目录的 .env.local 中填写高德 Web JS API Key。',
);

let AMapApi: AMapNamespace | null = null;
let map: AMapMap | null = null;
let heatMap: AMapHeatMap | null = null;
let markers: AMapMarker[] = [];
let resizeObserver: ResizeObserver | null = null;
let geocodeDiagnosticCount = 0;
let hasAutoFit = false;

const cityCenters: Record<string, [number, number]> = {
  南京市: [118.7969, 32.0603], 无锡市: [120.3119, 31.4912], 徐州市: [117.2841, 34.2058],
  常州市: [119.9741, 31.8112], 苏州市: [120.5853, 31.2989], 南通市: [120.8943, 31.9802],
  连云港市: [119.2216, 34.5967], 淮安市: [119.0153, 33.6104], 盐城市: [120.1636, 33.3474],
  扬州市: [119.4128, 32.3944], 镇江市: [119.4258, 32.1878], 泰州市: [119.9231, 32.4558],
  宿迁市: [118.2752, 33.963],
};

function distanceKm(a: [number, number], b: { lng: number; lat: number }): number {
  const radians = (value: number) => value * Math.PI / 180;
  const latDistance = radians(b.lat - a[1]);
  const lngDistance = radians(b.lng - a[0]);
  const value = Math.sin(latDistance / 2) ** 2
    + Math.cos(radians(a[1])) * Math.cos(radians(b.lat)) * Math.sin(lngDistance / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(value));
}

function isPlausibleLocation(project: AmapProjectPoint, location: { lng: number; lat: number }): boolean {
  // 当前项目库为江苏数据；没有城市信息时不把模糊搜索结果当作精确点位。
  if (!project.city || !cityCenters[project.city]) return false;
  if (location.lng < 116.2 || location.lng > 122.1 || location.lat < 30.7 || location.lat > 35.2) return false;
  return distanceKm(cityCenters[project.city]!, location) <= 160;
}

function groupRating(group: typeof locatedProjects.value): AmapProjectPoint['rating'] {
  const scores = { A: 100, B: 75, C: 50, D: 20 } as const;
  const values = group.flatMap((item) => item.rating ? [scores[item.rating]] : []);
  if (!values.length) return '';
  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  return average >= 87.5 ? 'A' : average >= 62.5 ? 'B' : average >= 35 ? 'C' : 'D';
}

function buildMarkerContent(
  project: AmapProjectPoint & { precise?: boolean },
  projectCount = 1,
  expandedOffset?: { x: number; y: number },
  labelOverride?: string,
): HTMLElement {
  const expanded = Boolean(expandedOffset);
  const marker = document.createElement('button');
  marker.type = 'button';
  marker.className = `amap-project-marker ${projectCount > 1 ? 'project-cluster' : ''} ${expanded ? 'project-expanded' : ''} ${project.rating ? `rating-${project.rating.toLowerCase()}` : 'rating-unrated'} ${project.precise ? '' : 'location-approximate'}`;
  marker.setAttribute(
    'aria-label',
    projectCount > 1
      ? `${project.city || project.district}区域参考点位，共${projectCount}个项目`
      : `${project.name}，${project.rating || '未评级'}项目，${project.precise ? '地址解析点位' : '区域参考点位'}`,
  );
  const grade = document.createElement('b');
  grade.textContent = labelOverride ?? (projectCount > 1 ? String(projectCount) : project.rating || '·');
  const pulse = document.createElement('i');
  marker.append(grade, pulse);
  if (expandedOffset) {
    const dx = expandedOffset.x + 15;
    const dy = expandedOffset.y + 15;
    marker.style.setProperty('--leader-length', `${Math.hypot(dx, dy)}px`);
    marker.style.setProperty('--leader-angle', `${Math.atan2(-dy, -dx)}rad`);
  }
  return marker;
}

function clearMarkers(): void {
  if (map && markers.length) map.remove(markers);
  markers.forEach((marker) => marker.setMap(null));
  markers = [];
}

function renderProjects(): void {
  if (!AMapApi || !map) return;
  clearMarkers();

  const coordinateGroups = new Map<string, typeof locatedProjects.value>();
  locatedProjects.value.forEach((project) => {
    const key = `${project.lng.toFixed(6)},${project.lat.toFixed(6)}`;
    const group = coordinateGroups.get(key) ?? [];
    group.push(project);
    coordinateGroups.set(key, group);
  });

  markers = (props.displayMode === 'count' ? [] : [...coordinateGroups.values()]).flatMap((group) => {
    const project = group[0]!;
    // 少量项目即使落在完全相同的坐标，也必须保持“一项目一点位”。
    // 用固定像素半径错开展示，既不会把项目合并丢失，也不会随地图缩放改变真实坐标。
    // 只有大量项目共用城市兜底坐标时才继续聚合，避免再次出现全图放射线。
    if (group.length > 1 && group.length <= 8) {
      const radius = group.length <= 3 ? 30 : 38;
      return group.map((item, index) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * index) / group.length;
        const expandedOffset = {
          x: Math.round(Math.cos(angle) * radius),
          y: Math.round(Math.sin(angle) * radius),
        };
        const content = buildMarkerContent(item, 1, expandedOffset);
        content.addEventListener('click', (event) => {
          event.stopPropagation();
          emit('projectClick', item);
        });
        return new AMapApi!.Marker({
          position: [item.lng, item.lat],
          content,
          offset: new AMapApi!.Pixel(expandedOffset.x - 15, expandedOffset.y - 15),
          title: item.name,
          zIndex: item.rating === 'A' ? 121 : 101,
        });
      });
    }
    if (group.length > 1) {
      // 多个项目使用同一城市/区域回退坐标时必须聚合。旧逻辑把它们按同心圆
      // 展开，项目较多时会形成横竖放射线，并让评级点位完全遮住地图。
      const aggregateRating = groupRating(group);
      const aggregateProject = { ...project, rating: aggregateRating };
      const content = buildMarkerContent(aggregateProject, group.length, undefined, aggregateRating || '·');
      content.addEventListener('click', (event) => {
        event.stopPropagation();
        emit('projectClick', project);
      });
      return [new AMapApi!.Marker({
        position: [project.lng, project.lat],
        content,
        offset: new AMapApi!.Pixel(-20, -20),
        title: `${project.city || project.district || '该区域'}：${group.length}个项目`,
        zIndex: 110,
      })];
    }
    const content = buildMarkerContent(project, group.length);
    content.addEventListener('click', (event) => {
      event.stopPropagation();
      emit('projectClick', project);
    });
    const marker = new AMapApi!.Marker({
      position: [project.lng, project.lat],
      content,
      offset: new AMapApi!.Pixel(group.length > 1 ? -20 : -15, group.length > 1 ? -20 : -15),
      title: group.length > 1 ? `${project.city || project.district}：${group.length}个项目` : project.name,
      zIndex: project.rating === 'A' ? 120 : 100,
    });
    return [marker];
  });

  if (markers.length) map.add(markers);

  // 以约20公里网格聚合热力点。精确地址和城市回退点使用同一统计尺度，
  // 再用平方根压缩极端城市数量，避免一个回退坐标吞掉全省其他热点。
  const heatGridSize = 0.18;
  const heatGrid = new Map<string, { lngSum: number; latSum: number; count: number }>();
  locatedProjects.value.forEach((project) => {
    const key = `${Math.round(project.lng / heatGridSize)},${Math.round(project.lat / heatGridSize)}`;
    const cell = heatGrid.get(key) ?? { lngSum: 0, latSum: 0, count: 0 };
    cell.lngSum += project.lng;
    cell.latSum += project.lat;
    cell.count += 1;
    heatGrid.set(key, cell);
  });
  const heatData = [...heatGrid.values()].map((cell) => ({
    lng: cell.lngSum / cell.count,
    lat: cell.latSum / cell.count,
    count: Math.sqrt(cell.count),
  }));
  heatMap?.setDataSet({
    data: heatData,
    max: Math.max(1, ...heatData.map((item) => item.count)),
  });
  if (props.displayMode === 'count' && heatData.length) heatMap?.show();
  else heatMap?.hide();

  // 只在评级/跟踪点位第一次出现时自动取景。后台分批定位会重复渲染，
  // 不能持续 setFitView，否则用户滚轮缩放后地图会自动退回。
  if (markers.length && !hasAutoFit) {
    map.setFitView(markers, false, [56, 90, 56, 90]);
    hasAutoFit = true;
  }
}

const locationCacheKey = 'bidding-amap-geocodes-v2';
function readLocationCache(): Record<number, { lng: number; lat: number; precise: boolean }> {
  try {
    return JSON.parse(localStorage.getItem(locationCacheKey) || '{}') as Record<
      number,
      { lng: number; lat: number; precise: boolean }
    >;
  } catch {
    return {};
  }
}

function locationQueries(project: AmapProjectPoint): string[] {
  const region = `${project.province}${project.city}${project.district}`;
  const landmark =
    project.name.match(/^(.+?校区)/)?.[1] ??
    project.name.match(/^(.+?(?:大学|学院|学校|医院|广场|园区|景区|中心))/)?.[1];
  return [...new Set([
    `${region}${project.name}`,
    landmark ? `${region}${landmark}` : '',
    project.owner ? `${region}${project.owner}` : '',
  ].filter(Boolean))];
}

function geocode(address: string, city: string): Promise<{ lng: number; lat: number } | null> {
  if (!AMapApi?.Geocoder) return Promise.resolve(null);
  const geocoder = new AMapApi.Geocoder({ city });
  return new Promise((resolve) => {
    let settled = false;
    const finish = (value: { lng: number; lat: number } | null) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      resolve(value);
    };
    const timeoutId = window.setTimeout(() => finish(null), 4500);
    geocoder.getLocation(address, (status, result) => {
      const location = status === 'complete' ? result.geocodes?.[0]?.location : undefined;
      if (!location && geocodeDiagnosticCount < 3) {
        geocodeDiagnosticCount += 1;
        console.warn('AMap Geocoder未返回点位', JSON.stringify({ status, result }));
      }
      finish(location ? { lng: location.getLng(), lat: location.getLat() } : null);
    });
  });
}

function searchPlace(keyword: string, city: string): Promise<{ lng: number; lat: number } | null> {
  if (!AMapApi?.PlaceSearch) return Promise.resolve(null);
  const placeSearch = new AMapApi.PlaceSearch({ city, citylimit: true, pageSize: 1 });
  return new Promise((resolve) => {
    let settled = false;
    const finish = (value: { lng: number; lat: number } | null) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      resolve(value);
    };
    const timeoutId = window.setTimeout(() => finish(null), 4500);
    placeSearch.search(keyword, (status, result) => {
      const location = status === 'complete' ? result.poiList?.pois?.[0]?.location : undefined;
      if (!location && geocodeDiagnosticCount < 6) {
        geocodeDiagnosticCount += 1;
        console.warn('AMap PlaceSearch未返回点位', JSON.stringify({ status, result }));
      }
      finish(location ? { lng: location.getLng(), lat: location.getLat() } : null);
    });
  });
}

async function persistLocation(
  project: AmapProjectPoint,
  location: { lng: number; lat: number },
  source: string,
): Promise<void> {
  if (!project.dbId) return;
  try {
    await fetch(`/api/projects/${project.dbId}/location`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ longitude: location.lng, latitude: location.lat, level: 'poi', source }),
    });
  } catch {
    // 地图仍可使用本次解析结果；服务恢复后会在下次打开时重试入库。
  }
}

async function resolveProjectLocations(): Promise<void> {
  const cache = readLocationCache();
  displayProjects.value.forEach((project) => {
    if (
      project.locationPrecision
      && project.locationPrecision !== 'city'
      && isPlausibleLocation(project, { lng: project.lng, lat: project.lat })
    ) {
      cache[project.id] = { lng: project.lng, lat: project.lat, precise: true };
    }
  });
  resolvedLocations.value = { ...cache };
  const pending = displayProjects.value.filter((project) => !cache[project.id]?.precise);
  const batchSize = 5;
  for (let start = 0; start < pending.length; start += batchSize) {
    await Promise.all(
      pending.slice(start, start + batchSize).map(async (project) => {
        let location: { lng: number; lat: number } | null = null;
        let source = 'AMap.Geocoder';
        for (const query of locationQueries(project)) {
          location = await geocode(query, project.city);
          if (location && isPlausibleLocation(project, location)) break;
          location = null;
        }
        if (!location) {
          source = 'AMap.PlaceSearch';
          for (const query of locationQueries(project)) {
            location = await searchPlace(query.replace(`${project.province}${project.city}${project.district}`, ''), project.city);
            if (location && isPlausibleLocation(project, location)) break;
            location = null;
          }
        }
        cache[project.id] = location
          ? { ...location, precise: true }
          : { lng: project.lng, lat: project.lat, precise: false };
        if (location) void persistLocation(project, location, source);
      }),
    );
    resolvedLocations.value = { ...cache };
    renderProjects();
  }
  localStorage.setItem(locationCacheKey, JSON.stringify(cache));
}

async function initializeMap(): Promise<void> {
  if (!container.value || !amapKey) return;
  loading.value = true;
  errorMessage.value = '';

  if (securityCode) window._AMapSecurityConfig = { securityJsCode: securityCode };

  try {
    AMapApi = (await AMapLoader.load({
      key: amapKey,
      version: '2.0',
      plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.HeatMap', 'AMap.Geocoder', 'AMap.PlaceSearch'],
    })) as AMapNamespace;
    await new Promise<void>((resolve) => {
      AMapApi!.plugin(['AMap.Geocoder', 'AMap.PlaceSearch'], resolve);
    });
    map = new AMapApi.Map(container.value, {
      center: [104.195397, 35.86166],
      zoom: 4.6,
      mapStyle: 'amap://styles/darkblue',
      viewMode: '3D',
      pitch: 20,
      features: ['bg', 'road', 'building', 'point'],
    });
    map.addControl(new AMapApi.Scale({ position: 'LB' }));
    map.addControl(
      new AMapApi.ToolBar({ position: { top: '64px', right: '12px' }, liteStyle: true }),
    );
    heatMap = new AMapApi.HeatMap(map, {
      radius: 34,
      opacity: [0.1, 0.86],
      gradient: {
        0.2: '#1557c0',
        0.45: '#00b5f5',
        0.7: '#22e3c3',
        0.88: '#ffd05d',
        1: '#ff536e',
      },
    });
    ready.value = true;
    renderProjects();
    void resolveProjectLocations();
    resizeObserver = new ResizeObserver(() => map?.resize());
    resizeObserver.observe(container.value);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '请检查高德 Key、网络或安全配置。';
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.projects, props.displayMode],
  () => {
    renderProjects();
    void resolveProjectLocations();
  },
  { deep: true },
);

onMounted(() => void initializeMap());

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  clearMarkers();
  map?.destroy();
  map = null;
  AMapApi = null;
});
</script>

<style scoped lang="scss">
.amap-project-map,
.amap-container {
  position: absolute;
  width: 100%;
  height: 100%;
  inset: 0;
}
.amap-project-map {
  overflow: hidden;
  background: #031532;
}
.amap-container {
  background: radial-gradient(circle at center, rgb(16 103 201 / 18%), transparent 57%), #031532;
}
.map-state {
  position: absolute;
  z-index: 3;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 9px;
  color: #78cfff;
  background:
    radial-gradient(circle at center, rgb(15 98 196 / 22%), transparent 50%), rgb(3 21 50 / 92%);
  text-align: center;
}
.map-state strong {
  color: #dff6ff;
  font-size: 17px;
  font-weight: 600;
}
.map-state small {
  max-width: 360px;
  color: #90b4d2;
  font-size: 13px;
  line-height: 1.7;
}
.map-state code {
  padding: 6px 9px;
  color: #5fc8f5;
  background: rgb(10 76 142 / 28%);
  border: 1px solid rgb(56 157 226 / 20%);
  border-radius: 3px;
  font-size: 11px;
}
.map-state--error {
  color: #ff738b;
}
.state-spinner {
  width: 27px;
  height: 27px;
  border: 2px solid rgb(80 192 248 / 20%);
  border-top-color: #50c0f8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.layer-controls {
  position: absolute;
  z-index: 2;
  top: 12px;
  left: 12px;
  display: flex;
  gap: 6px;
}
.layer-controls button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 34px;
  padding: 0 12px;
  color: #91b5d3;
  background: rgb(3 27 63 / 88%);
  border: 1px solid rgb(62 148 220 / 24%);
  border-radius: 3px;
  font: inherit;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(8px);
}
.layer-controls button.active {
  color: #d8f6ff;
  background: rgb(12 104 196 / 76%);
  border-color: rgb(64 194 252 / 45%);
}
.gis-summary {
  position: absolute;
  z-index: 2;
  right: 13px;
  bottom: 13px;
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 7px 10px;
  color: #88aecc;
  background: rgb(3 24 57 / 88%);
  border: 1px solid rgb(59 146 216 / 20%);
  border-radius: 3px;
  font-size: 11px;
  backdrop-filter: blur(8px);
}
.gis-summary strong {
  color: #55d7ff;
  font-size: 17px;
}
.gis-empty-state {
  position: absolute;
  z-index: 2;
  top: 50%;
  left: 50%;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 12px 16px;
  color: #9dc2db;
  background: rgb(3 24 57 / 90%);
  border: 1px solid rgb(67 168 230 / 28%);
  border-radius: 4px;
  font-size: 12px;
  transform: translate(-50%, -50%);
  backdrop-filter: blur(8px);
}

:global(.amap-project-marker) {
  position: relative;
  display: grid;
  width: 30px;
  height: 30px;
  padding: 0;
  place-items: center;
  color: #fff;
  background: #18bde9;
  border: 2px solid rgb(195 244 255 / 85%);
  border-radius: 50% 50% 50% 8px;
  box-shadow: 0 0 18px rgb(22 190 234 / 70%);
  transform: rotate(-45deg);
  cursor: pointer;
}
:global(.amap-project-marker b) {
  z-index: 1;
  font-size: 10px;
  transform: rotate(45deg);
}
:global(.amap-project-marker i) {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 1px solid currentcolor;
  border-radius: 50%;
  animation: marker-pulse 1.7s ease-out infinite;
}
:global(.amap-project-marker.rating-b) {
  background: #347cf0;
  box-shadow: 0 0 18px rgb(52 124 240 / 66%);
}
:global(.amap-project-marker.rating-c) {
  background: #e6a92f;
  box-shadow: 0 0 18px rgb(230 169 47 / 60%);
}
:global(.amap-project-marker.rating-d) {
  background: #e95470;
  box-shadow: 0 0 18px rgb(233 84 112 / 60%);
}
:global(.amap-project-marker.location-approximate) {
  opacity: 0.58;
  border-style: dashed;
  box-shadow: none;
}
:global(.amap-project-marker.project-cluster) {
  width: 40px;
  height: 40px;
  color: #e8fbff;
  background: rgb(12 117 190 / 92%);
  border: 2px solid #7ee8ff;
  border-radius: 50%;
  opacity: 1;
  box-shadow: 0 0 0 5px rgb(33 190 235 / 18%), 0 0 24px rgb(20 174 226 / 62%);
  transform: none;
}
:global(.amap-project-marker.project-cluster b) {
  font-size: 12px;
  transform: none;
}
:global(.amap-project-marker.project-cluster i) {
  animation: marker-pulse 2s ease-out infinite;
}
:global(.amap-project-marker.project-expanded) {
  border-radius: 50%;
  transform: none;
  box-shadow: 0 0 0 4px rgb(3 21 50 / 72%), 0 0 18px rgb(22 190 234 / 70%);
}
:global(.amap-project-marker.project-expanded::before) {
  position: absolute;
  z-index: -1;
  top: 50%;
  left: 50%;
  width: var(--leader-length);
  height: 1px;
  content: '';
  background: linear-gradient(90deg, rgb(111 221 255 / 82%), rgb(111 221 255 / 20%));
  transform: rotate(var(--leader-angle));
  transform-origin: 0 50%;
  pointer-events: none;
}
:global(.amap-project-marker.project-expanded b) {
  transform: none;
}
:global(.amap-project-marker.project-expanded i) {
  animation: none;
  opacity: 0.35;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
@keyframes marker-pulse {
  to {
    opacity: 0;
    transform: scale(1.8);
  }
}
</style>
