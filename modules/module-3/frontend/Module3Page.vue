<template>
  <q-page class="business-page result-workbench">
    <div class="page-title-row">
      <div>
        <div class="page-eyebrow">Bid result intelligence</div>
        <h1 class="page-title">投标结果与复盘分析</h1>
        <p class="page-description">录入开标事实、评分差距、原因判断、整改行动和知识更新审批</p>
      </div>
      <div class="header-actions">
        <label class="secondary"
          ><q-icon name="upload_file" />导入投标人 CSV<input
            type="file"
            accept=".csv"
            @change="importCsv" /></label
        ><button class="secondary" @click="resetCase"><q-icon name="add" />新建</button
        ><button class="primary" :disabled="saving" @click="saveCase">
          <q-icon name="save" />{{ saving ? '保存中' : '保存事实版本' }}
        </button>
      </div>
    </div>
    <div v-if="message" class="notice" :class="{ error: messageType === 'error' }">
      {{ message }}
    </div>
    <div class="workspace-grid">
      <aside class="tech-panel case-list">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="history" />复盘项目</h2>
          <span class="panel-meta">{{ cases.length }} 项</span>
        </div>
        <button
          v-for="item in cases"
          :key="item.id"
          :class="{ active: item.id === form.id }"
          @click="loadCase(item.id)"
        >
          <strong>{{ item.projectName }}</strong
          ><span>{{ item.sectionCode }} · 第{{ item.bidRound }}轮</span
          ><small>V{{ item.version }} · {{ item.updatedAt }}</small>
        </button>
        <div v-if="!cases.length" class="empty">暂无复盘记录</div>
      </aside>
      <main class="main-column">
        <section class="tech-panel">
          <div class="panel-heading">
            <h2 class="panel-title"><q-icon name="fact_check" />项目与比较口径</h2>
            <span class="panel-meta">同标段 · 同轮次 · 同税费 · 同费用范围</span>
          </div>
          <div class="form-grid">
            <label><span>项目名称</span><input v-model="form.projectName" /></label
            ><label><span>省份</span><input v-model="form.province" /></label
            ><label><span>城市</span><input v-model="form.city" /></label
            ><label><span>工程专业</span><input v-model="form.profession" /></label
            ><label><span>工程类型</span><input v-model="form.projectType" /></label
            ><label
              ><span>项目等级</span
              ><select v-model="form.projectGrade">
                <option>A</option>
                <option>B</option>
                <option>C</option>
              </select></label
            ><label><span>标段编号</span><input v-model="form.scope.sectionCode" /></label
            ><label><span>招标轮次</span><input v-model="form.scope.bidRound" /></label
            ><label><span>税费口径</span><input v-model="form.scope.taxBasis" /></label
            ><label><span>费用范围</span><input v-model="form.scope.costBasis" /></label
            ><label
              ><span>招标控制价 元</span
              ><input v-model.number="form.controlPrice" type="number" /></label
            ><label><span>开标日期</span><input v-model="form.openingDate" type="date" /></label
            ><label><span>操作人</span><input v-model="form.operator" /></label
            ><label class="wide"
              ><span>版本说明</span
              ><input
                v-model="form.changeReason"
                placeholder="说明新增或修正依据；历史版本不会被覆盖"
            /></label>
          </div>
        </section>
        <nav class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <q-icon :name="tab.icon" />{{ tab.label }}
          </button>
        </nav>

        <section v-if="activeTab === 'bids'" class="tech-panel data-panel">
          <PanelTitle
            icon="leaderboard"
            title="投标报价与候选排名"
            action="新增投标人"
            @action="addBid"
          />
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>投标人</th>
                  <th>报价</th>
                  <th>修正价</th>
                  <th>评标价</th>
                  <th>有效性</th>
                  <th>候选排名</th>
                  <th>我方</th>
                  <th>中标</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(bid, index) in form.bids" :key="bid.localId">
                  <td><input v-model="bid.bidderName" /></td>
                  <td><input v-model.number="bid.quotedPrice" type="number" /></td>
                  <td><input v-model.number="bid.correctedPrice" type="number" /></td>
                  <td><input v-model.number="bid.evaluatedPrice" type="number" /></td>
                  <td>
                    <select v-model="bid.validity">
                      <option value="valid">有效</option>
                      <option value="invalid">无效</option>
                      <option value="pending">待确认</option>
                    </select>
                  </td>
                  <td><input v-model.number="bid.candidateRank" type="number" /></td>
                  <td>
                    <input
                      v-model="bid.isOurs"
                      type="checkbox"
                      @change="exclusive('isOurs', index)"
                    />
                  </td>
                  <td>
                    <input
                      v-model="bid.isWinner"
                      type="checkbox"
                      @change="exclusive('isWinner', index)"
                    />
                  </td>
                  <td>
                    <button class="danger" @click="form.bids.splice(index, 1)">
                      <q-icon name="delete" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="metrics">
            <article>
              <span>我方下浮率</span><b>{{ percent(priceMetrics.discountRate) }}</b>
            </article>
            <article>
              <span>与中标价差</span><b>{{ money(priceMetrics.winnerPriceDifference) }}</b>
            </article>
            <article>
              <span>相对价差</span><b>{{ percent(priceMetrics.relativePriceDifference) }}</b>
            </article>
            <article>
              <span>下浮率差</span><b>{{ percent(priceMetrics.discountRateDifference) }}</b>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'scores'" class="tech-panel data-panel">
          <PanelTitle
            icon="score"
            title="分项评分与材料差异"
            action="新增评分项"
            @action="addScore"
          />
          <div class="table-wrap score-table">
            <table>
              <thead>
                <tr>
                  <th>投标人</th>
                  <th>类别</th>
                  <th>评分项</th>
                  <th>原始分</th>
                  <th>折算分</th>
                  <th>阶段分</th>
                  <th>最终分</th>
                  <th>满分</th>
                  <th>证据位置</th>
                  <th>材料差异</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(score, index) in form.scores" :key="score.localId">
                  <td>
                    <select v-model="score.bidderName">
                      <option v-for="bid in form.bids" :key="bid.localId" :value="bid.bidderName">
                        {{ bid.bidderName || '未命名' }}
                      </option>
                    </select>
                  </td>
                  <td>
                    <select v-model="score.category">
                      <option v-for="item in scoreCategories" :key="item.value" :value="item.value">
                        {{ item.label }}
                      </option>
                    </select>
                  </td>
                  <td><input v-model="score.itemName" /></td>
                  <td><input v-model.number="score.rawScore" type="number" /></td>
                  <td><input v-model.number="score.convertedScore" type="number" /></td>
                  <td><input v-model.number="score.stageScore" type="number" /></td>
                  <td><input v-model.number="score.finalScore" type="number" /></td>
                  <td><input v-model.number="score.maxScore" type="number" /></td>
                  <td><input v-model="score.evidence" /></td>
                  <td><input v-model="score.materialDifference" /></td>
                  <td>
                    <button class="danger" @click="form.scores.splice(index, 1)">
                      <q-icon name="delete" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="gap-list">
            <h3>我方与领先单位差距</h3>
            <article v-for="gap in scoreGaps" :key="gap.itemName">
              <b>{{ categoryLabel(gap.category) }} · {{ gap.itemName }}</b
              ><span
                >我方 {{ gap.ourFinalScore }} / 领先方 {{ gap.leaderFinalScore }} / 差距
                {{ gap.scoreGap }}</span
              >
              <p>{{ gap.materialDifference || '暂无材料差异说明' }}</p>
            </article>
            <div v-if="!scoreGaps.length" class="empty">录入我方与中标方同名评分项后自动对比</div>
          </div>
        </section>

        <section v-else-if="activeTab === 'causes'" class="tech-panel data-panel">
          <PanelTitle
            icon="manage_search"
            title="原因归纳与证据来源"
            action="新增原因"
            @action="addCause"
          />
          <div class="card-list">
            <article v-for="(cause, index) in form.causes" :key="cause.localId">
              <div>
                <select v-model="cause.category">
                  <option v-for="item in causeCategories" :key="item.value" :value="item.value">
                    {{ item.label }}
                  </option></select
                ><select v-model="cause.sourceType">
                  <option value="official">官方记录</option>
                  <option value="internal">公司判断</option>
                  <option value="ai">AI建议</option></select
                ><button class="danger" @click="form.causes.splice(index, 1)">
                  <q-icon name="delete" />
                </button>
              </div>
              <textarea v-model="cause.description" placeholder="原因描述"></textarea
              ><input v-model="cause.evidence" placeholder="证据来源、页码或记录位置" />
            </article>
            <div v-if="!form.causes.length" class="empty">尚未归纳原因</div>
          </div>
        </section>

        <section v-else-if="activeTab === 'analytics'" class="tech-panel data-panel">
          <div class="panel-heading">
            <h2 class="panel-title"><q-icon name="analytics" />跨项目统计分析</h2>
            <span class="panel-meta">仅使用已保存事实版本</span>
          </div>
          <div class="analytics-kpis">
            <article>
              <span>累计投标</span><b>{{ analytics.total }}</b>
            </article>
            <article>
              <span>中标项目</span><b>{{ analytics.wins }}</b>
            </article>
            <article>
              <span>整体中标率</span><b>{{ percent(analytics.winRate) }}</b>
            </article>
            <article>
              <span>平均中标下浮率</span><b>{{ percent(analytics.averageDiscount) }}</b>
            </article>
          </div>
          <div class="analytics-grid">
            <div>
              <h3>区域中标表现</h3>
              <article v-for="row in analytics.regions" :key="row.name">
                <span>{{ row.name }}</span
                ><b>{{ row.wins }}/{{ row.total }} · {{ percent(row.rate) }}</b>
              </article>
            </div>
            <div>
              <h3>专业中标表现</h3>
              <article v-for="row in analytics.professions" :key="row.name">
                <span>{{ row.name }}</span
                ><b>{{ row.wins }}/{{ row.total }} · {{ percent(row.rate) }}</b>
              </article>
            </div>
            <div>
              <h3>未中标/废标原因</h3>
              <article v-for="row in analytics.causes" :key="row.name">
                <span>{{ categoryLabel(row.name) }}</span
                ><b>{{ row.count }} 次</b>
              </article>
            </div>
          </div>
        </section>

        <section v-else class="tech-panel data-panel">
          <PanelTitle
            icon="task_alt"
            title="改进措施与知识更新"
            action="新增改进措施"
            @action="addImprovement"
          />
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>类别</th>
                  <th>改进措施</th>
                  <th>责任人</th>
                  <th>截止日期</th>
                  <th>状态</th>
                  <th>目标</th>
                  <th>实施效果</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in form.improvements" :key="item.localId">
                  <td>
                    <select v-model="item.category">
                      <option
                        v-for="category in causeCategories"
                        :key="category.value"
                        :value="category.value"
                      >
                        {{ category.label }}
                      </option>
                    </select>
                  </td>
                  <td><input v-model="item.action" /></td>
                  <td><input v-model="item.owner" /></td>
                  <td><input v-model="item.dueDate" type="date" /></td>
                  <td>
                    <select v-model="item.status">
                      <option value="todo">待执行</option>
                      <option value="doing">执行中</option>
                      <option value="done">已完成</option>
                      <option value="verified">已验证</option>
                    </select>
                  </td>
                  <td><input v-model="item.target" /></td>
                  <td><input v-model="item.effect" /></td>
                  <td>
                    <button class="danger" @click="form.improvements.splice(index, 1)">
                      <q-icon name="delete" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="knowledge">
            <div>
              <h3>提交知识更新申请</h3>
              <label
                ><span>更新对象</span
                ><select v-model="knowledge.targetType">
                  <option value="template">标书模板</option>
                  <option value="cost_parameter">成本参数</option>
                  <option value="experience_rule">经验规则</option>
                </select></label
              ><label><span>对象名称</span><input v-model="knowledge.targetName" /></label
              ><label><span>建议变更</span><textarea v-model="knowledge.proposedChange" /></label
              ><button class="primary" :disabled="!form.id" @click="submitKnowledge">
                提交审核
              </button>
            </div>
            <div>
              <h3>审核记录</h3>
              <article v-for="request in knowledgeRequests" :key="request.id">
                <b>{{ targetLabel(request.target_type) }} · {{ request.target_name }}</b
                ><span :class="`status-${request.status}`">{{ statusLabel(request.status) }}</span>
                <p>{{ request.proposed_change }}</p>
                <div v-if="request.status === 'pending'">
                  <input v-model="reviewer" placeholder="审核人" /><button
                    @click="reviewKnowledge(request.id, true)"
                  >
                    通过</button
                  ><button @click="reviewKnowledge(request.id, false)">驳回</button>
                </div>
              </article>
              <div v-if="!knowledgeRequests.length" class="empty">
                只有审核通过后，模板、成本参数和经验规则才进入受控更新流程。
              </div>
            </div>
          </div>
        </section>

        <section v-if="versions.length" class="tech-panel">
          <div class="panel-heading">
            <h2 class="panel-title"><q-icon name="lock_clock" />历史事实版本</h2>
            <span class="panel-meta">只追加，不覆盖</span>
          </div>
          <div class="versions">
            <article v-for="item in versions" :key="item.version">
              <b>V{{ item.version }}</b
              ><span>{{ item.reason }}</span
              ><small>{{ item.createdBy }} · {{ item.createdAt }}</small>
            </article>
          </div>
        </section>
      </main>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue';
const PanelTitle = defineComponent({
  props: { icon: String, title: String, action: String },
  emits: ['action'],
  setup(props, { emit }) {
    return () =>
      h('div', { class: 'panel-heading' }, [
        h('h2', { class: 'panel-title' }, [
          h('i', { class: `q-icon material-icons` }, props.icon),
          props.title,
        ]),
        h('button', { class: 'link-button', onClick: () => emit('action') }, props.action),
      ]);
  },
});
type Bid = {
  localId: number;
  bidderName: string;
  quotedPrice: number;
  correctedPrice: number;
  evaluatedPrice: number;
  validity: string;
  candidateRank: number;
  isOurs: boolean;
  isWinner: boolean;
};
type Form = {
  id: number | null;
  projectName: string;
  province: string;
  city: string;
  profession: string;
  projectType: string;
  projectGrade: string;
  controlPrice: number;
  openingDate: string;
  operator: string;
  changeReason: string;
  scope: { sectionCode: string; bidRound: string; taxBasis: string; costBasis: string };
  bids: Bid[];
  scores: any[];
  causes: any[];
  improvements: any[];
};
const tabs = [
  { key: 'bids', label: '报价与排名', icon: 'leaderboard' },
  { key: 'scores', label: '评分与差距', icon: 'score' },
  { key: 'causes', label: '原因与证据', icon: 'psychology' },
  { key: 'analytics', label: '大数据分析', icon: 'analytics' },
  { key: 'actions', label: '整改与更新', icon: 'published_with_changes' },
];
const scoreCategories = [
  { value: 'price', label: '报价' },
  { value: 'technical', label: '技术' },
  { value: 'commercial', label: '商务' },
  { value: 'personnel', label: '人员' },
  { value: 'performance', label: '业绩' },
  { value: 'credit', label: '信用' },
  { value: 'qualification', label: '资格' },
];
const causeCategories = [
  { value: 'price', label: '价格' },
  { value: 'technical', label: '技术' },
  { value: 'qualification', label: '资格' },
  { value: 'commercial', label: '商务' },
  { value: 'process', label: '流程' },
];
const activeTab = ref('bids'),
  saving = ref(false),
  message = ref(''),
  messageType = ref('success'),
  cases = ref<any[]>([]),
  versions = ref<any[]>([]),
  knowledgeRequests = ref<any[]>([]),
  reviewer = ref('');
let serial = 1;
const id = () => serial++;
const blankBid = (name = ''): Bid => ({
  localId: id(),
  bidderName: name,
  quotedPrice: 0,
  correctedPrice: 0,
  evaluatedPrice: 0,
  validity: 'valid',
  candidateRank: 0,
  isOurs: false,
  isWinner: false,
});
const blank = (): Form => ({
  id: null,
  projectName: '',
  province: '',
  city: '',
  profession: '',
  projectType: '',
  projectGrade: 'C',
  controlPrice: 0,
  openingDate: '',
  operator: '',
  changeReason: '首次录入开标与评标事实',
  scope: { sectionCode: '', bidRound: '1', taxBasis: '含税', costBasis: '全费用口径' },
  bids: [blankBid('我方'), blankBid('中标单位')],
  scores: [],
  causes: [],
  improvements: [],
});
const form = reactive<Form>(blank());
form.bids[0]!.isOurs = true;
form.bids[1]!.isWinner = true;
form.bids[1]!.candidateRank = 1;
const knowledge = reactive({ targetType: 'template', targetName: '', proposedChange: '' });
const ours = computed(() => form.bids.find((x) => x.isOurs)),
  winner = computed(
    () => form.bids.find((x) => x.isWinner) || form.bids.find((x) => x.candidateRank === 1),
  );
const price = (x?: Bid) => Number(x?.evaluatedPrice || x?.correctedPrice || x?.quotedPrice || 0);
const priceMetrics = computed(() => {
  const a = price(ours.value),
    b = price(winner.value),
    c = Number(form.controlPrice || 0),
    d = c && a ? ((c - a) / c) * 100 : null,
    w = c && b ? ((c - b) / c) * 100 : null;
  return {
    discountRate: d,
    winnerPriceDifference: a && b ? a - b : null,
    relativePriceDifference: a && b ? ((a - b) / b) * 100 : null,
    discountRateDifference: d !== null && w !== null ? d - w : null,
  };
});
const analytics = computed(() => {
  const records = cases.value;
  const won = (item: any) => {
    const our = item.bids?.find((bid: any) => bid.isOurs);
    const winner =
      item.bids?.find((bid: any) => bid.isWinner) ||
      item.bids?.find((bid: any) => +bid.candidateRank === 1);
    return Boolean(our && winner && our.bidderName === winner.bidderName);
  };
  const group = (field: string) => {
    const map = new Map<string, { name: string; total: number; wins: number; rate: number }>();
    records.forEach((item: any) => {
      const name = String(item[field] || '未分类');
      const row = map.get(name) || { name, total: 0, wins: 0, rate: 0 };
      row.total++;
      if (won(item)) row.wins++;
      row.rate = row.total ? (row.wins / row.total) * 100 : 0;
      map.set(name, row);
    });
    return [...map.values()].sort((a, b) => b.total - a.total);
  };
  const discounts = records
    .map((item: any) => {
      const winner =
        item.bids?.find((bid: any) => bid.isWinner) ||
        item.bids?.find((bid: any) => +bid.candidateRank === 1);
      const value = Number(
          winner?.evaluatedPrice || winner?.correctedPrice || winner?.quotedPrice || 0,
        ),
        control = Number(item.controlPrice || 0);
      return control && value ? ((control - value) / control) * 100 : null;
    })
    .filter((value: any): value is number => value !== null);
  const causeMap = new Map<string, number>();
  records
    .filter((item: any) => !won(item))
    .flatMap((item: any) => item.causes || [])
    .forEach((cause: any) => causeMap.set(cause.category, (causeMap.get(cause.category) || 0) + 1));
  const wins = records.filter(won).length;
  return {
    total: records.length,
    wins,
    winRate: records.length ? (wins / records.length) * 100 : null,
    averageDiscount: discounts.length
      ? discounts.reduce((a: number, b: number) => a + b, 0) / discounts.length
      : null,
    regions: group('province'),
    professions: group('profession'),
    causes: [...causeMap]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count),
  };
});
const scoreGaps = computed(() =>
  form.scores
    .filter((x) => x.bidderName === ours.value?.bidderName)
    .map((x) => {
      const y = form.scores.find(
        (z) =>
          z.bidderName === winner.value?.bidderName &&
          z.category === x.category &&
          z.itemName === x.itemName,
      );
      return y
        ? {
            ...x,
            ourFinalScore: +x.finalScore || 0,
            leaderFinalScore: +y.finalScore || 0,
            scoreGap: (+y.finalScore || 0) - (+x.finalScore || 0),
            materialDifference: x.materialDifference || y.materialDifference,
          }
        : null;
    })
    .filter(Boolean),
);
const notify = (text: string, type = 'success') => {
  message.value = text;
  messageType.value = type;
  setTimeout(() => {
    if (message.value === text) message.value = '';
  }, 6000);
};
const money = (v: number | null) =>
  v === null
    ? '—'
    : new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(v);
const percent = (v: number | null) => (v === null ? '—' : `${v.toFixed(2)}%`);
const categoryLabel = (v: string) => scoreCategories.find((x) => x.value === v)?.label || v;
const targetLabel = (v: string) =>
  (({ template: '标书模板', cost_parameter: '成本参数', experience_rule: '经验规则' }) as any)[v] ||
  v;
const statusLabel = (v: string) =>
  (({ pending: '待审核', approved: '已通过', rejected: '已驳回', applied: '已应用' }) as any)[v] ||
  v;
function addBid() {
  form.bids.push(blankBid());
}
function addScore() {
  form.scores.push({
    localId: id(),
    bidderName: ours.value?.bidderName || '',
    category: 'technical',
    itemName: '',
    rawScore: 0,
    convertedScore: 0,
    stageScore: 0,
    finalScore: 0,
    maxScore: 0,
    evidence: '',
    materialDifference: '',
  });
}
function addCause() {
  form.causes.push({
    localId: id(),
    category: 'price',
    sourceType: 'official',
    description: '',
    evidence: '',
  });
}
function addImprovement() {
  form.improvements.push({
    localId: id(),
    category: 'price',
    action: '',
    owner: '',
    dueDate: '',
    status: 'todo',
    target: '',
    effect: '',
  });
}
function exclusive(field: 'isOurs' | 'isWinner', index: number) {
  if (!form.bids[index]?.[field]) return;
  form.bids.forEach((x, i) => {
    if (i !== index) x[field] = false;
  });
}
function resetCase() {
  Object.assign(form, blank());
  form.bids[0]!.isOurs = true;
  form.bids[1]!.isWinner = true;
  form.bids[1]!.candidateRank = 1;
  versions.value = [];
  knowledgeRequests.value = [];
  activeTab.value = 'bids';
}
function hydrate(data: any) {
  const fresh = blank();
  Object.assign(form, fresh, data, {
    id: +data.id,
    scope: { ...fresh.scope, ...data.scope },
    bids: (data.bids || []).map((x: any) => ({ ...x, localId: id() })),
    scores: (data.scores || []).map((x: any) => ({ ...x, localId: id() })),
    causes: (data.causes || []).map((x: any) => ({ ...x, localId: id() })),
    improvements: (data.improvements || []).map((x: any) => ({ ...x, localId: id() })),
  });
}
async function refresh() {
  const r = await fetch('/api/results/cases'),
    b = await r.json();
  if (!r.ok) throw Error(b.message || '读取失败');
  cases.value = b.data || [];
}
async function loadCase(caseId: number) {
  try {
    const r = await fetch(`/api/results/cases/${caseId}`),
      b = await r.json();
    if (!r.ok) throw Error(b.message || '读取失败');
    hydrate(b.data);
    versions.value = b.versions || [];
    knowledgeRequests.value = b.knowledgeRequests || [];
  } catch (e) {
    notify(e instanceof Error ? e.message : '读取失败', 'error');
  }
}
async function saveCase() {
  saving.value = true;
  try {
    const r = await fetch('/api/results/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      }),
      b = await r.json();
    if (!r.ok) throw Error(b.message || '保存失败');
    notify(b.message);
    await refresh();
    await loadCase(b.id);
  } catch (e) {
    notify(e instanceof Error ? e.message : '保存失败', 'error');
  } finally {
    saving.value = false;
  }
}
const csv = (line: string) => {
  const out: string[] = [],
    chars = [...line];
  let value = '',
    quoted = false;
  for (let i = 0; i < chars.length; i++) {
    const c = chars[i];
    if (c === '"' && chars[i + 1] === '"') {
      value += '"';
      i++;
    } else if (c === '"') quoted = !quoted;
    else if (c === ',' && !quoted) {
      out.push(value.trim());
      value = '';
    } else value += c;
  }
  out.push(value.trim());
  return out;
};
async function importCsv(event: Event) {
  const input = event.target as HTMLInputElement,
    file = input.files?.[0];
  if (!file) return;
  try {
    const lines = (await file.text())
        .replace(/^\uFEFF/, '')
        .split(/\r?\n/)
        .filter(Boolean),
      headers = csv(lines.shift() || ''),
      aliases: any = {
        投标人: 'bidderName',
        报价: 'quotedPrice',
        修正价: 'correctedPrice',
        评标价: 'evaluatedPrice',
        有效性: 'validity',
        候选排名: 'candidateRank',
        我方: 'isOurs',
        中标: 'isWinner',
      };
    form.bids = lines.map((line) => {
      const bid: any = blankBid();
      csv(line).forEach((v, i) => {
        const key = aliases[headers[i] || ''] || headers[i];
        if (['quotedPrice', 'correctedPrice', 'evaluatedPrice', 'candidateRank'].includes(key))
          bid[key] = +v || 0;
        else if (['isOurs', 'isWinner'].includes(key)) bid[key] = ['1', '是', 'true'].includes(v);
        else if (key === 'validity')
          bid[key] = v === '无效' ? 'invalid' : v === '待确认' ? 'pending' : 'valid';
        else if (key) bid[key] = v;
      });
      return bid;
    });
    notify(`已导入 ${form.bids.length} 家投标人`);
  } catch {
    notify('CSV解析失败，请检查标准表头', 'error');
  } finally {
    input.value = '';
  }
}
async function submitKnowledge() {
  try {
    const r = await fetch(`/api/results/cases/${form.id}/knowledge-requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...knowledge, requestedBy: form.operator }),
      }),
      b = await r.json();
    if (!r.ok) throw Error(b.message || '提交失败');
    knowledge.targetName = '';
    knowledge.proposedChange = '';
    await loadCase(form.id!);
    notify('已提交审核');
  } catch (e) {
    notify(e instanceof Error ? e.message : '提交失败', 'error');
  }
}
async function reviewKnowledge(requestId: number, approved: boolean) {
  try {
    const r = await fetch(`/api/results/knowledge-requests/${requestId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, reviewer: reviewer.value }),
      }),
      b = await r.json();
    if (!r.ok) throw Error(b.message || '审核失败');
    await loadCase(form.id!);
    notify(approved ? '已审核通过' : '已驳回');
  } catch (e) {
    notify(e instanceof Error ? e.message : '审核失败', 'error');
  }
}
onMounted(() =>
  refresh().catch((e) => notify(e instanceof Error ? e.message : '数据库不可用', 'error')),
);
</script>

<style scoped lang="scss">
.result-workbench {
  padding-bottom: 28px;
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.primary,
.secondary,
.link-button {
  display: inline-flex;
  height: 36px;
  padding: 0 14px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #effaff;
  background: linear-gradient(180deg, #168fea, #0d5fbd);
  border: 1px solid rgb(71 194 255/50%);
  border-radius: 4px;
  cursor: pointer;
}
.secondary {
  color: #a8d6ef;
  background: #092e59;
  border-color: #256590;
}
.secondary input {
  display: none;
}
.primary:disabled {
  opacity: 0.4;
}
.notice {
  margin-bottom: 12px;
  padding: 10px;
  color: #86e8c3;
  background: #0b493e;
  border: 1px solid #257d69;
}
.notice.error {
  color: #ff9caf;
  background: #4b1830;
  border-color: #8c304c;
}
.workspace-grid {
  display: grid;
  grid-template-columns: 245px minmax(0, 1fr);
  gap: 14px;
}
.main-column {
  display: grid;
  gap: 14px;
  min-width: 0;
}
.case-list {
  align-self: start;
  overflow: hidden;
}
.case-list > button {
  display: grid;
  width: 100%;
  gap: 4px;
  padding: 13px 15px;
  color: #8eafc8;
  text-align: left;
  background: transparent;
  border: 0;
  border-bottom: 1px solid rgb(56 119 170/18%);
  cursor: pointer;
}
.case-list > button.active {
  background: #0b3b69;
  box-shadow: inset 3px 0 #38c9ef;
}
.case-list strong {
  color: #dcefff;
}
.case-list small {
  color: #557b9b;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px;
}
.form-grid label,
.knowledge label {
  display: grid;
  gap: 5px;
}
.form-grid span,
.knowledge label span {
  color: #7fa5c1;
  font-size: 10px;
}
.form-grid .wide {
  grid-column: span 2;
}
.tabs {
  display: flex;
  gap: 6px;
  padding: 8px;
  background: #071f45;
  border: 1px solid #1b527d;
}
.tabs button {
  display: flex;
  gap: 6px;
  padding: 9px 15px;
  color: #799fbd;
  background: transparent;
  border: 1px solid transparent;
}
.tabs button.active {
  color: #fff;
  background: #0a4c82;
  border-color: #2c7fae;
}
.data-panel {
  min-width: 0;
}
:deep(.link-button) {
  display: inline-flex;
  height: 30px;
  padding: 0 12px;
  align-items: center;
  justify-content: center;
  color: #5ddcff;
  background: transparent;
  border: 1px solid #26729e;
  border-radius: 4px;
  cursor: pointer;
}
.table-wrap {
  margin: 16px;
  overflow: auto;
  border: 1px solid #194f7a;
}
.table-wrap table {
  width: 100%;
  min-width: 1050px;
  border-collapse: collapse;
}
.score-table table {
  min-width: 1450px;
}
.table-wrap th,
.table-wrap td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid rgb(56 119 170/24%);
  font-size: 10px;
}
.table-wrap th {
  color: #9cc4df;
  background: #0a2d58;
}
.table-wrap td input:not([type='checkbox']),
.table-wrap td select {
  width: 100%;
}
input,
select,
textarea {
  min-width: 0;
  color: #e6f5ff;
  background: #061d40;
  border: 1px solid #205786;
  border-radius: 3px;
}
input,
select {
  height: 34px;
  padding: 0 8px;
}
textarea {
  min-height: 78px;
  padding: 8px;
}
.danger {
  width: 30px;
  height: 30px;
  color: #ff8097;
  background: transparent;
  border: 1px solid #71324b;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 0 16px 16px;
}
.metrics article {
  display: grid;
  gap: 6px;
  padding: 14px;
  background: #082650;
  border: 1px solid #1b527d;
}
.metrics span {
  color: #799fbd;
}
.metrics b {
  color: #f0faff;
  font-size: 17px;
}
.analytics-kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 16px;
}
.analytics-kpis article {
  display: grid;
  gap: 7px;
  padding: 15px;
  background: #082650;
  border: 1px solid #1b527d;
}
.analytics-kpis span,
.analytics-grid span {
  color: #799fbd;
  font-size: 11px;
}
.analytics-kpis b {
  color: #64dcff;
  font-size: 20px;
}
.analytics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 0 16px 16px;
}
.analytics-grid > div {
  min-height: 180px;
  padding: 14px;
  background: #071f45;
  border: 1px solid #1b527d;
}
.analytics-grid h3 {
  margin: 0 0 10px;
  color: #dcefff;
  font-size: 14px;
}
.analytics-grid article {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid rgb(50 111 160/25%);
}
.analytics-grid b {
  color: #e3f4ff;
  font-size: 11px;
}
.gap-list {
  display: grid;
  gap: 8px;
  padding: 0 16px 16px;
}
.gap-list h3,
.knowledge h3 {
  margin: 0;
  color: #dcefff;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}
.gap-list article {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 5px;
  padding: 12px;
  background: #071f45;
  border: 1px solid #1b527d;
}
.gap-list p {
  grid-column: 1/-1;
  margin: 0;
}
.card-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 16px;
}
.card-list article {
  display: grid;
  gap: 8px;
  padding: 12px;
  background: #071f45;
  border: 1px solid #1b527d;
}
.card-list article > div {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 8px;
}
.knowledge {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 16px;
  padding: 0 16px 16px;
}
.knowledge > div {
  display: grid;
  align-content: start;
  gap: 10px;
  padding: 14px;
  background: #071f45;
  border: 1px solid #1b527d;
}
.knowledge article {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px;
  padding: 10px;
  border-bottom: 1px solid #1b527d;
}
.knowledge article p,
.knowledge article div {
  grid-column: 1/-1;
}
.knowledge article div {
  display: flex;
  gap: 7px;
}
.status-pending {
  color: #ffbd63;
}
.status-approved {
  color: #5ee2b3;
}
.status-rejected {
  color: #ff8499;
}
.versions {
  display: flex;
  gap: 10px;
  padding: 14px;
  overflow: auto;
}
.versions article {
  display: grid;
  min-width: 220px;
  gap: 4px;
  padding: 11px;
  background: #071f45;
  border: 1px solid #1b527d;
}
.versions b {
  color: #5fd6f7;
}
.empty {
  padding: 18px;
  color: #577d9d;
  text-align: center;
}
@media (max-width: 1100px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }
  .case-list {
    display: none;
  }
  .form-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .knowledge {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 700px) {
  .form-grid,
  .metrics,
  .card-list {
    grid-template-columns: 1fr;
  }
  .form-grid .wide {
    grid-column: auto;
  }
  .tabs {
    overflow: auto;
  }
  .tabs button {
    white-space: nowrap;
  }
}
</style>
