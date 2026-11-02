<template>
  <section class="tech-panel method-five-panel">
    <div class="panel-heading">
      <h2 class="panel-title"><q-icon name="calculate" />ABC 合成法模拟评分</h2>
      <span class="panel-meta">METHOD 5 · AUDITABLE SIMULATION</span>
    </div>

    <div class="rule-note">
      A/B/C、规定范围、K、Δ及暂估价扣除按当前规则原型计算；软件模拟抽取不等同于开标或评标现场的官方抽取。
    </div>

    <div class="parameter-grid">
      <label>工程分类<select v-model="category"><option v-for="item in categories" :key="item.key" :value="item.key">{{ item.label }}</option></select></label>
      <label>最高投标限价（元）<input v-model="maximum" inputmode="decimal" /></label>
      <label>专业工程暂估价含税（元）<input v-model="provisional" inputmode="decimal" /></label>
      <label>下浮率 Δ<select v-model.number="delta"><option v-for="rate in currentDeltas" :key="rate" :value="rate">{{ rate }}%</option></select></label>
      <label>下浮系数 K<select v-model.number="coefficient"><option v-for="rate in coefficients" :key="rate" :value="rate">{{ rate }}%</option></select></label>
      <label>报价满分（可配置）<input v-model="baseScore" inputmode="decimal" /></label>
      <label>高于基准每 1% 扣分<input v-model="upperDeduction" inputmode="decimal" /></label>
      <label>低于基准每 1% 扣分<input v-model="lowerDeduction" inputmode="decimal" /></label>
    </div>

    <div class="bid-toolbar">
      <div><strong>第二阶段有效评标价</strong><small>输入含专业工程暂估价的修正后评标价</small></div>
      <button type="button" class="secondary" @click="addBidder"><q-icon name="add" />添加投标人</button>
    </div>
    <div class="bid-table-wrap">
      <table>
        <thead><tr><th>序号</th><th>投标人</th><th>评标价（含暂估价）</th><th></th></tr></thead>
        <tbody>
          <tr v-for="(bidder, index) in bidders" :key="bidder.id">
            <td>{{ index + 1 }}</td>
            <td><input v-model="bidder.name" /></td>
            <td><input v-model="bidder.price" inputmode="decimal" /></td>
            <td><button type="button" class="icon-button" :disabled="bidders.length <= 3" @click="bidders.splice(index, 1)"><q-icon name="delete_outline" /></button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="error" class="calc-error">{{ error }}</div>
    <div class="calc-actions">
      <button type="button" class="secondary" @click="randomizeParameters">随机抽取 K、Δ</button>
      <button type="button" class="primary" @click="calculate">计算并模拟抽取 B</button>
    </div>

    <template v-if="result">
      <div class="result-metrics">
        <article><span>规定范围下限</span><strong>{{ money(result.lowerBound) }}</strong></article>
        <article><span>A 值</span><strong>{{ money(result.a) }}</strong></article>
        <article><span>B 值</span><strong>{{ money(result.b) }}</strong><small>{{ result.bName }}</small></article>
        <article><span>C 值</span><strong>{{ money(result.c) }}</strong></article>
        <article class="benchmark"><span>评标基准价</span><strong>{{ money(result.benchmark) }}</strong></article>
      </div>
      <div class="audit-line">
        有效报价 {{ result.eligibleCount }} 家；B 候选：95%–92% 区间 {{ result.bandOneCount }} 家、92%–89% 区间 {{ result.bandTwoCount }} 家、89% 以下 {{ result.belowCount }} 家<span v-if="result.fallback">；本次启用兜底候选范围</span>。
      </div>
      <div class="score-table-wrap">
        <table>
          <thead><tr><th>名次</th><th>投标人</th><th>扣暂估价后评标价</th><th>偏差率</th><th>扣分</th><th>报价得分</th><th>范围状态</th></tr></thead>
          <tbody><tr v-for="row in result.rows" :key="row.id"><td>{{ row.rank }}</td><td>{{ row.name }}</td><td>{{ money(row.netPrice) }}</td><td>{{ row.deviation.toFixed(4) }}%</td><td>{{ row.deduction.toFixed(2) }}</td><td><b>{{ row.score.toFixed(2) }}</b></td><td :class="row.eligible ? 'eligible' : 'excluded'">{{ row.eligible ? '规定范围内' : '不参与 B/C 抽取' }}</td></tr></tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';

type Bidder = { id: number; name: string; price: string };
type ScoreRow = { id: number; name: string; netPrice: number; eligible: boolean; deviation: number; deduction: number; score: number; rank: number };
type CalculationResult = { lowerBound: number; a: number; b: number; bName: string; c: number; benchmark: number; eligibleCount: number; bandOneCount: number; bandTwoCount: number; belowCount: number; fallback: boolean; rows: ScoreRow[] };

const categories = [
  { key: 'building', label: '房屋建筑工程', deltas: [6, 7, 8, 9, 10, 11, 12] },
  { key: 'decoration', label: '装饰装修、建筑幕墙、钢结构工程', deltas: [8, 9, 10, 11, 12, 13, 14, 15] },
  { key: 'mechanical', label: '机电安装工程', deltas: [9, 10, 11, 12, 13, 14, 15, 16] },
  { key: 'municipal', label: '市政工程', deltas: [12, 13, 14, 15, 16, 17, 18, 19, 20] },
  { key: 'landscape', label: '绿化工程', deltas: [17, 18, 19, 20, 21, 22, 23, 24, 25] },
];
const coefficients = [95, 95.5, 96, 96.5, 97, 97.5, 98];
const category = ref('building');
const currentDeltas = computed(() => categories.find((item) => item.key === category.value)?.deltas ?? []);
const maximum = ref('10000000');
const provisional = ref('0');
const delta = ref(6);
const coefficient = ref(95);
const baseScore = ref('82');
const upperDeduction = ref('0.9');
const lowerDeduction = ref('0.6');
let nextId = 5;
const bidders = reactive<Bidder[]>([
  { id: 1, name: '投标人一', price: '9000000' },
  { id: 2, name: '投标人二', price: '8700000' },
  { id: 3, name: '投标人三', price: '8400000' },
  { id: 4, name: '投标人四', price: '8100000' },
]);
const error = ref('');
const result = ref<CalculationResult | null>(null);

watch(category, () => { delta.value = currentDeltas.value[0] ?? 0; result.value = null; });
watch([maximum, provisional, delta, coefficient, baseScore, upperDeduction, lowerDeduction], () => { result.value = null; });

function round(value: number) { return Math.round((value + Number.EPSILON) * 100) / 100; }
function numberValue(value: string, label: string) { const parsed = Number(value.replaceAll(',', '').trim()); if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`${label}必须是非负数字`); return round(parsed); }
function pick<T>(items: T[]) { return items[Math.floor(Math.random() * items.length)]!; }
function money(value: number) { return `${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 元`; }
function addBidder() { bidders.push({ id: nextId++, name: `投标人${bidders.length + 1}`, price: '' }); result.value = null; }
function randomizeParameters() { delta.value = pick(currentDeltas.value); coefficient.value = pick(coefficients); result.value = null; }

function calculate() {
  try {
    error.value = '';
    if (bidders.length < 3) throw new Error('至少需要 3 家第二阶段有效报价');
    const max = numberValue(maximum.value, '最高投标限价');
    const provisionalValue = numberValue(provisional.value, '专业工程暂估价');
    if (provisionalValue >= max) throw new Error('专业工程暂估价必须小于最高投标限价');
    const seen = new Set<string>();
    const records = bidders.map((bidder, index) => {
      const name = bidder.name.trim();
      if (!name) throw new Error(`第 ${index + 1} 家投标人名称不能为空`);
      if (seen.has(name)) throw new Error(`投标人名称重复：${name}`);
      seen.add(name);
      const price = numberValue(bidder.price, `${name}评标价`);
      if (price > max) throw new Error(`${name}评标价超过最高投标限价`);
      const netPrice = round(price - provisionalValue);
      if (netPrice <= 0) throw new Error(`${name}扣除暂估价后的评标价必须大于 0`);
      return { ...bidder, name, netPrice };
    });
    const netMaximum = round(max - provisionalValue);
    const mean = records.reduce((sum, row) => sum + row.netPrice, 0) / records.length;
    const lowerBound = round((mean * 0.7 + netMaximum * 0.3) * 0.75);
    const eligible = records.filter((row) => row.netPrice >= lowerBound);
    if (eligible.length < 2) throw new Error('规定范围内报价不足，无法抽取 B/C');
    const c = Math.min(...eligible.map((row) => row.netPrice));
    const withoutC = eligible.filter((row) => row.netPrice !== c);
    if (!withoutC.length) throw new Error('排除最低价 C 后没有可用 B，需按招标文件或现场规则处理');
    const a = round(netMaximum * (1 - delta.value / 100));
    const bandOne = withoutC.filter((row) => row.netPrice < a * 0.95 && row.netPrice >= a * 0.92);
    const bandTwo = withoutC.filter((row) => row.netPrice < a * 0.92 && row.netPrice >= a * 0.89);
    const below = withoutC.filter((row) => row.netPrice < a * 0.89);
    let pool = [...(bandOne.length ? [pick(bandOne)] : []), ...(bandTwo.length ? [pick(bandTwo)] : []), ...below];
    const fallback = pool.length === 0;
    if (fallback) pool = withoutC;
    const selectedB = pick(pool);
    const benchmark = round((a * 0.5 + selectedB.netPrice * 0.3 + c * 0.2) * (coefficient.value / 100));
    const full = numberValue(baseScore.value, '报价满分');
    const upper = numberValue(upperDeduction.value, '高于基准扣分');
    const lower = numberValue(lowerDeduction.value, '低于基准扣分');
    const rows: ScoreRow[] = records.map((row) => {
      const deviation = ((row.netPrice - benchmark) / benchmark) * 100;
      const deduction = Math.abs(deviation) * (deviation > 0 ? upper : lower);
      return { id: row.id, name: row.name, netPrice: row.netPrice, eligible: row.netPrice >= lowerBound, deviation, deduction, score: Math.max(0, round(full - deduction)), rank: 0 };
    }).sort((left, right) => right.score - left.score || left.netPrice - right.netPrice);
    rows.forEach((row, index) => { row.rank = index > 0 && row.score === rows[index - 1]!.score && row.netPrice === rows[index - 1]!.netPrice ? rows[index - 1]!.rank : index + 1; });
    result.value = { lowerBound, a, b: selectedB.netPrice, bName: selectedB.name, c, benchmark, eligibleCount: eligible.length, bandOneCount: bandOne.length, bandTwoCount: bandTwo.length, belowCount: below.length, fallback, rows };
  } catch (cause) {
    result.value = null;
    error.value = cause instanceof Error ? cause.message : '计算失败';
  }
}
</script>

<style scoped lang="scss">
.method-five-panel{margin-top:16px}.rule-note{margin:14px 18px 0;padding:12px 14px;color:#9ec5df;background:rgb(7 47 91/65%);border-left:3px solid #44cbea;font-size:12px}.parameter-grid{display:grid;grid-template-columns:repeat(4,minmax(170px,1fr));gap:12px;padding:18px}.parameter-grid label{display:grid;gap:7px;color:#87abc8;font-size:11px}.parameter-grid input,.parameter-grid select,.bid-table-wrap input{width:100%;height:38px;padding:0 10px;color:#e5f5ff;background:#061d40;border:1px solid #205786;border-radius:3px;outline:none}.parameter-grid input:focus,.parameter-grid select:focus,.bid-table-wrap input:focus{border-color:#42cdec}.bid-toolbar{display:flex;padding:0 18px 12px;align-items:center;justify-content:space-between}.bid-toolbar div{display:grid}.bid-toolbar strong{color:#e2f4ff;font-size:14px}.bid-toolbar small{color:#6e94b4;font-size:10px}.secondary,.primary,.icon-button{display:inline-flex;align-items:center;justify-content:center;gap:5px;height:36px;padding:0 13px;color:#a8d6ef;background:#092e59;border:1px solid #256590;border-radius:3px;cursor:pointer}.primary{color:#fff;background:linear-gradient(90deg,#087fc7,#11a9da);border-color:#2ab9e8}.bid-table-wrap,.score-table-wrap{margin:0 18px;overflow:auto;border:1px solid #194f7a}.bid-table-wrap table,.score-table-wrap table{width:100%;border-collapse:collapse}.bid-table-wrap th,.bid-table-wrap td,.score-table-wrap th,.score-table-wrap td{padding:9px 11px;text-align:left;border-bottom:1px solid rgb(56 119 170/24%);font-size:11px}.bid-table-wrap th,.score-table-wrap th{color:#9cc4df;background:#0a2d58;white-space:nowrap}.bid-table-wrap th:first-child{width:58px}.bid-table-wrap th:last-child{width:52px}.icon-button{width:34px;padding:0;color:#ff8499}.icon-button:disabled{opacity:.3}.calc-actions{display:flex;gap:10px;padding:15px 18px;justify-content:flex-end}.calc-error{margin:12px 18px 0;padding:10px;color:#ff91a4;background:rgb(148 27 57/18%);border:1px solid rgb(255 83 116/28%);font-size:11px}.result-metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:5px 18px 14px}.result-metrics article{display:grid;min-height:82px;padding:13px;align-content:center;background:#082650;border:1px solid #1b527d}.result-metrics span{color:#7fa4c1;font-size:10px}.result-metrics strong{margin-top:6px;color:#eaf8ff;font-size:17px}.result-metrics small{color:#65ccec;font-size:9px}.result-metrics .benchmark{background:linear-gradient(135deg,rgb(9 113 155/55%),rgb(10 54 105/75%));border-color:#2da5ce}.audit-line{margin:0 18px 12px;padding:10px;color:#8fb4ce;background:#061d3e;font-size:10px}.score-table-wrap{margin-bottom:18px}.score-table-wrap b{color:#4be0b6}.eligible{color:#47d9af}.excluded{color:#ffb65e}@media(max-width:1100px){.parameter-grid{grid-template-columns:repeat(2,1fr)}.result-metrics{grid-template-columns:repeat(3,1fr)}}@media(max-width:620px){.parameter-grid,.result-metrics{grid-template-columns:1fr}.bid-toolbar{align-items:flex-start;gap:10px;flex-direction:column}}
</style>
