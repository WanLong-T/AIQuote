<template>
  <q-page class="business-page">
    <div class="page-title-row">
      <div>
        <div class="page-eyebrow">Bid result intelligence</div>
        <h1 class="page-title">投标结果分析</h1>
        <p class="page-description">复盘投标表现，识别竞争差距并沉淀下一次投标策略</p>
      </div>
      <div class="status-pill">分析模型待数据</div>
    </div>

    <div class="result-metrics">
      <article v-for="metric in metrics" :key="metric.label" class="tech-panel result-card">
        <q-icon :name="metric.icon" size="21px" />
        <div>
          <span>{{ metric.label }}</span
          ><strong>{{ metric.value }}</strong>
        </div>
        <em>{{ metric.note }}</em>
      </article>
    </div>

    <div class="analysis-grid">
      <section class="tech-panel ranking-panel">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="leaderboard" />竞争报价对比</h2>
          <span class="panel-meta">PRICE RANKING</span>
        </div>
        <div class="rank-chart">
          <div v-for="(bar, index) in bars" :key="bar" class="rank-row">
            <span>{{ index + 1 }}</span
            ><i :style="{ width: `${bar}%` }" /><b>等待数据</b>
          </div>
        </div>
      </section>
      <section class="tech-panel insight-panel">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="psychology" />AI 复盘洞察</h2>
          <span class="panel-meta">AI INSIGHT</span>
        </div>
        <div class="insight-empty">
          <q-icon name="auto_awesome" size="38px" /><strong>暂无分析结果</strong
          ><span>录入投标结果后，系统将生成差距分析和改进建议</span
          ><button type="button">录入投标结果</button>
        </div>
      </section>
    </div>
  </q-page>
</template>

<script setup lang="ts">
const metrics = [
  { label: '参与项目', value: '—', note: '累计投标项目', icon: 'folder_open' },
  { label: '中标项目', value: '—', note: '成功中标数量', icon: 'workspace_premium' },
  { label: '综合中标率', value: '— %', note: '投标转化表现', icon: 'donut_large' },
  { label: '平均排名', value: '—', note: '同类项目排名', icon: 'military_tech' },
];
const bars = [82, 69, 57, 44, 31];
</script>

<style scoped lang="scss">
.result-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.result-card {
  display: grid;
  min-height: 112px;
  grid-template-columns: 43px 1fr;
  align-items: center;
  gap: 10px;
  padding: 18px;
}
.result-card > .q-icon {
  display: grid;
  width: 43px;
  height: 43px;
  place-items: center;
  color: #5dd4ff;
  background: rgb(24 129 220 / 18%);
  border: 1px solid rgb(67 184 249 / 22%);
  border-radius: 5px;
}
.result-card span {
  display: block;
  color: #82a8c9;
  font-size: 11px;
}
.result-card strong {
  display: block;
  margin-top: 4px;
  color: #f4faff;
  font-size: 24px;
  font-weight: 600;
}
.result-card em {
  grid-column: 2;
  color: #466f94;
  font-size: 9px;
  font-style: normal;
}
.analysis-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}
.ranking-panel,
.insight-panel {
  min-height: 430px;
}
.rank-chart {
  display: grid;
  gap: 24px;
  padding: 44px 28px;
}
.rank-row {
  display: grid;
  grid-template-columns: 24px 1fr 75px;
  align-items: center;
  gap: 10px;
  color: #5680a7;
  font-size: 10px;
}
.rank-row > span {
  color: #50bcf3;
  font-size: 12px;
}
.rank-row i {
  height: 9px;
  background: linear-gradient(90deg, #1267d4, #31d6f1);
  border-radius: 2px;
  box-shadow: 0 0 12px rgb(32 182 255 / 22%);
  opacity: 0.75;
}
.rank-row b {
  font-weight: 400;
}
.insight-empty {
  display: grid;
  min-height: 370px;
  align-content: center;
  justify-items: center;
  gap: 10px;
  padding: 30px;
  color: #5180a7;
  text-align: center;
}
.insight-empty .q-icon {
  color: #49ccff;
  filter: drop-shadow(0 0 12px rgb(55 177 255 / 28%));
}
.insight-empty strong {
  color: #dcefff;
  font-size: 16px;
  font-weight: 500;
}
.insight-empty span {
  max-width: 320px;
  font-size: 11px;
  line-height: 1.8;
}
.insight-empty button {
  margin-top: 12px;
  padding: 9px 22px;
  color: #ecfaff;
  background: linear-gradient(180deg, #168fea, #0d5fbd);
  border: 1px solid rgb(71 194 255 / 50%);
  border-radius: 4px;
  font: inherit;
  cursor: pointer;
}
@media (max-width: 1000px) {
  .result-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 560px) {
  .result-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
