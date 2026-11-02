<template>
  <q-page class="business-page">
    <div class="page-title-row">
      <div>
        <div class="page-eyebrow">Bid template simulation</div>
        <h1 class="page-title">投标模板模拟分析</h1>
        <p class="page-description">智能提取招标文件要点，生成投标框架并进行模拟评审</p>
      </div>
      <label class="upload-trigger"><q-icon name="upload_file" />导入招标文件<input type="file" accept=".pdf,.doc,.docx" @change="selectTenderFile" /></label>
    </div>

    <section class="tech-panel extraction-panel">
      <div class="panel-heading">
        <h2 class="panel-title"><q-icon name="document_scanner" />招标文件智能提取</h2>
        <span class="panel-meta">DOCUMENT INTELLIGENCE</span>
      </div>
      <div class="template-layout">
        <div class="info-table">
          <div
            v-for="(row, index) in fields"
            :key="row.label"
            class="info-row"
            :class="{ 'info-row--active': index === 0 }"
          >
            <div class="info-label"><q-icon :name="row.icon" />{{ row.label }}</div>
            <div class="info-value">{{ row.value }}</div>
          </div>
        </div>
        <aside class="outline-card">
          <h3>模拟标书框架</h3>
          <div
            v-for="(item, index) in outline"
            :key="item"
            class="outline-item"
            :class="{ 'outline-item--active': index === 2 }"
          >
            <q-icon name="description" />{{ item }}
          </div>
        </aside>
      </div>
    </section>

    <section class="tech-panel library-panel">
      <div class="panel-heading">
        <h2 class="panel-title"><q-icon name="inventory_2" />标准化模板库</h2>
        <span class="panel-meta">6 类工程 · 5 类组成文件</span>
      </div>
      <div class="template-types">
        <button v-for="item in templateTypes" :key="item" type="button" :class="{ active: selectedType === item }" @click="selectedType = item">{{ item }}</button>
      </div>
      <div class="template-documents">
        <article v-for="item in outline" :key="item"><q-icon name="description" /><div><strong>{{ selectedType }} · {{ item }}</strong><span>标准章节、占位字段及符合性检查项</span></div><b>可用</b></article>
      </div>
    </section>

    <section class="tech-panel review-panel">
      <div class="panel-heading">
        <h2 class="panel-title"><q-icon name="rule" />模拟评审检查</h2>
      </div>
      <div class="review-items">
        <div v-for="item in checks" :key="item.label" class="review-item">
          <i :class="item.type" /><span>{{ item.label }}</span
          ><strong>{{ item.value }}</strong>
        </div>
      </div>
      <div class="actions">
        <button type="button" @click="generateVersions">生成三版本标书框架</button><button type="button" @click="showAdvice = !showAdvice">{{ showAdvice ? '收起评分建议' : '查看评分建议' }}</button>
      </div>
      <div v-if="generatedVersions.length" class="version-grid"><article v-for="version in generatedVersions" :key="version.name"><strong>{{ version.name }}</strong><span>{{ version.description }}</span><small>{{ version.sections }} 个章节 · {{ selectedType }}</small></article></div>
      <div v-if="showAdvice" class="advice-box"><strong>模拟专家评审建议</strong><p>优先逐条响应资格条件、评分项和否决条款；技术方案按评分细目建立一一对应目录。报价评分请使用下方 ABC 合成法计算器，并以项目招标文件实际评分参数覆盖默认值。</p></div>
    </section>
    <MethodFiveCalculator />
  </q-page>
</template>

<script setup lang="ts">
import MethodFiveCalculator from '../components/MethodFiveCalculator.vue';
import { computed, ref } from 'vue';

const selectedFile = ref<File | null>(null);
const selectedType = ref('房建');
const showAdvice = ref(false);
const generatedVersions = ref<{ name: string; description: string; sections: number }[]>([]);
const templateTypes = ['房建', '市政', '公路', '水利', '机电', '装饰装修'];
const fields = computed(() => [
  { label: '项目名称', value: selectedFile.value ? selectedFile.value.name.replace(/\.(pdf|docx?)$/i, '') : '等待上传招标文件', icon: 'badge' },
  { label: '资格要求', value: selectedFile.value ? '文件已导入，资格条件等待解析复核' : '系统将自动识别项目资质与业绩要求', icon: 'verified' },
  { label: '工期要求', value: selectedFile.value ? '等待从招标文件提取' : '—', icon: 'event_note' },
  { label: '评分重点', value: selectedFile.value ? '否决条款、资格条件、技术评分与报价评分' : '系统将提取技术方案与报价评分权重', icon: 'assignment' },
]);
const outline = ['资格审查资料', '技术标', '商务标', '报价函', '偏离表'];
const checks = [
  { label: '资质满足', value: '待检查', type: 'ok' },
  { label: '业绩满足', value: '待检查', type: 'ok' },
  { label: '工期满足', value: '待确认', type: 'warn' },
  { label: '废标风险点', value: '待识别', type: 'risk' },
];

function selectTenderFile(event: Event) {
  selectedFile.value = (event.target as HTMLInputElement).files?.[0] ?? null;
  generatedVersions.value = [];
}

function generateVersions() {
  generatedVersions.value = [
    { name: '标准版', description: '完整响应评分细则，保留全部证明材料与技术章节。', sections: 18 },
    { name: '精简版', description: '压缩重复内容，保留资格、否决项和核心评分响应。', sections: 12 },
    { name: '低价竞标版', description: '突出成本控制与报价策略，技术响应保持合规底线。', sections: 14 },
  ];
}
</script>

<style scoped lang="scss">
.extraction-panel {
  margin-bottom: 16px;
}
.upload-trigger{display:inline-flex;height:38px;padding:0 15px;align-items:center;gap:7px;color:#eefaff;background:linear-gradient(180deg,#168fea,#0d5fbd);border:1px solid rgb(71 194 255/50%);border-radius:4px;cursor:pointer}.upload-trigger input{display:none}.library-panel{margin-bottom:16px}.template-types{display:flex;gap:8px;padding:16px 18px 10px;flex-wrap:wrap}.template-types button{height:34px;padding:0 18px;color:#91b8d3;background:#082650;border:1px solid #1b527d;border-radius:3px;cursor:pointer}.template-types button.active{color:#fff;background:#0c6faf;border-color:#36c6ec}.template-documents{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:4px 18px 18px}.template-documents article{display:grid;grid-template-columns:30px 1fr auto;gap:8px;padding:13px;align-items:center;background:#071f45;border:1px solid rgb(56 135 193/25%)}.template-documents .q-icon{color:#4dd2f3;font-size:22px}.template-documents div{display:grid;gap:4px}.template-documents strong{color:#def2ff;font-size:11px}.template-documents span{color:#6f94b3;font-size:9px}.template-documents b{color:#42d9af;font-size:9px}.version-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:0 22px 18px}.version-grid article{display:grid;gap:6px;padding:14px;background:#082650;border:1px solid #1b527d}.version-grid strong{color:#eaf8ff}.version-grid span{color:#91b2ca;font-size:11px}.version-grid small{color:#46cdec}.advice-box{margin:0 22px 18px;padding:14px;color:#93b8d2;background:rgb(8 54 91/65%);border-left:3px solid #48caeb;font-size:11px}.advice-box strong{color:#e4f5ff}.advice-box p{margin:7px 0 0;line-height:1.8}
.template-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  padding: 15px;
}
.info-table {
  overflow: hidden;
  border: 1px solid rgb(78 170 244 / 24%);
  border-radius: 6px;
}
.info-row {
  display: grid;
  min-height: 78px;
  grid-template-columns: 210px 1fr;
  align-items: center;
  border-bottom: 1px solid rgb(83 153 218 / 13%);
}
.info-row:last-child {
  border-bottom: 0;
}
.info-row--active {
  background: linear-gradient(90deg, rgb(16 116 229 / 52%), rgb(19 83 172 / 27%));
}
.info-label {
  display: flex;
  height: 100%;
  align-items: center;
  gap: 10px;
  padding: 0 22px;
  color: #91b5d5;
  border-right: 1px solid rgb(83 153 218 / 15%);
}
.info-label .q-icon {
  color: #58c9ff;
}
.info-value {
  padding: 0 28px;
  color: #eef8ff;
  font-size: 15px;
}
.outline-card {
  min-height: 355px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgb(11 55 111 / 82%), rgb(5 34 76 / 88%));
  border: 1px solid rgb(74 171 245 / 32%);
  border-radius: 6px;
  box-shadow:
    inset 0 1px rgb(126 210 255 / 6%),
    0 10px 24px rgb(0 10 35 / 14%);
}
.outline-card h3 {
  margin: 0;
  padding: 16px 18px;
  color: #edf8ff;
  background: linear-gradient(90deg, rgb(16 83 158 / 88%), rgb(8 51 112 / 72%));
  border-bottom: 1px solid rgb(77 177 248 / 24%);
  font-size: 16px;
  font-weight: 600;
}
.outline-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  color: #b7d6ee;
  border-bottom: 1px solid rgb(69 145 211 / 12%);
  font-size: 13px;
  transition:
    color 160ms ease,
    background 160ms ease;
}
.outline-item:last-child {
  border-bottom: 0;
}
.outline-item:hover {
  color: #effaff;
  background: rgb(32 137 229 / 12%);
}
.outline-item .q-icon {
  color: #58c9ff;
}
.outline-item--active {
  color: #f5fbff;
  background:
    linear-gradient(90deg, rgb(23 137 235 / 42%), rgb(14 91 179 / 18%));
  box-shadow: inset 3px 0 #40c9ff;
}
.outline-item--active .q-icon {
  color: #7ee6ff;
  filter: drop-shadow(0 0 5px rgb(77 210 255 / 48%));
}
.review-panel {
  min-height: 205px;
}
.review-items {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 22px 22px 12px;
}
.review-item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0 10px;
  align-items: center;
  padding: 14px;
  background: rgb(4 29 67 / 28%);
  border: 1px solid rgb(72 150 222 / 15%);
  border-radius: 4px;
}
.review-item i {
  width: 12px;
  height: 12px;
  grid-row: span 2;
  background: #20d878;
  border-radius: 3px;
  box-shadow: 0 0 10px rgb(32 216 120 / 40%);
}
.review-item i.warn {
  background: #ffb43b;
  box-shadow: 0 0 10px rgb(255 180 59 / 40%);
}
.review-item i.risk {
  background: #ff5278;
  box-shadow: 0 0 10px rgb(255 82 120 / 40%);
}
.review-item span {
  color: #bfd5e8;
  font-size: 12px;
}
.review-item strong {
  margin-top: 3px;
  color: #557b9f;
  font-size: 10px;
  font-weight: 400;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 10px 22px 20px;
}
.actions button {
  padding: 9px 20px;
  color: #eefaff;
  background: linear-gradient(180deg, #168fea, #0d5fbd);
  border: 1px solid rgb(71 194 255 / 50%);
  border-radius: 4px;
  box-shadow:
    inset 0 1px rgb(255 255 255 / 12%),
    0 0 16px rgb(20 129 240 / 15%);
  font: inherit;
  cursor: pointer;
}
@media (max-width: 900px) {
  .template-layout {
    grid-template-columns: 1fr;
  }
  .outline-card {
    min-height: auto;
  }
  .review-items {
    grid-template-columns: repeat(2, 1fr);
  }
  .template-documents{grid-template-columns:repeat(2,1fr)}
}
@media (max-width: 560px) {
  .info-row {
    grid-template-columns: 125px 1fr;
  }
  .info-value {
    padding: 0 14px;
    font-size: 12px;
  }
  .review-items {
    grid-template-columns: 1fr;
  }
  .template-documents,.version-grid{grid-template-columns:1fr}
}
</style>
