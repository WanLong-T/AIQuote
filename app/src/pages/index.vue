<template>
  <q-page class="business-page dashboard-page">
    <div class="page-title-row dashboard-heading">
      <div>
        <div class="page-eyebrow">National project intelligence</div>
        <h1 class="page-title">全国项目可视化地图</h1>
        <p class="page-description">聚焦在招项目、投标截止预警与项目跟踪进度</p>
      </div>
      <div class="heading-actions">
        <div class="status-pill" :class="{ 'status-pill--demo': dataSourceMode !== 'live' }">
          {{ dataSourceLabel }}
        </div>
        <button type="button" class="history-button" @click="openUpdateHistory">
          <q-icon name="history" size="17px" />更新记录
        </button>
        <button type="button" class="ai-rating-button" @click="openAiRatingAssistant">
          <q-icon name="psychology" size="18px" />AI评级助手
        </button>
        <button type="button" class="primary-button" @click="exportLedger">
          <q-icon name="file_download" size="17px" />导出项目台账
        </button>
      </div>
    </div>

    <section class="filter-bar tech-panel">
      <label class="search-field">
        <q-icon name="search" size="18px" />
        <input
          v-model.trim="filters.keyword"
          type="search"
          placeholder="搜索项目名称、地区、业主单位或责任人"
          @keyup.enter="applyFilters"
        />
        <span v-if="appliedFilters.keyword && !filtersDirty" class="search-result-count">
          {{ filteredProjects.length }} 项
        </span>
      </label>
      <label class="filter-field">
        <span>项目范围</span>
        <q-select
          v-model="filters.scope"
          class="dashboard-select"
          :options="scopeOptions"
          emit-value
          map-options
          dense
          outlined
          options-dense
          popup-content-class="dashboard-select-popup"
          @update:model-value="applyScopeFilter"
        />
      </label>
      <label class="filter-field">
        <span>工程类别</span>
        <q-select
          v-model="filters.category"
          class="dashboard-select"
          :options="categoryOptions"
          emit-value
          map-options
          dense
          outlined
          options-dense
          popup-content-class="dashboard-select-popup"
        />
      </label>
      <label class="filter-field">
        <span>开标时间</span>
        <q-select
          v-model="filters.opening"
          class="dashboard-select"
          :options="openingOptions"
          emit-value
          map-options
          dense
          outlined
          options-dense
          popup-content-class="dashboard-select-popup"
        />
      </label>
      <label class="filter-field">
        <span>项目评级</span>
        <q-select
          v-model="filters.rating"
          class="dashboard-select"
          :options="ratingOptions"
          emit-value
          map-options
          dense
          outlined
          options-dense
          popup-content-class="dashboard-select-popup"
        />
      </label>
      <label class="filter-field">
        <span>跟踪状态</span>
        <q-select
          v-model="filters.status"
          class="dashboard-select"
          :options="statusOptions"
          emit-value
          map-options
          dense
          outlined
          options-dense
          popup-content-class="dashboard-select-popup"
        />
      </label>
      <button type="button" class="search-button" @click="applyFilters">
        <q-icon name="search" />检索
      </button>
      <button type="button" class="filter-button" @click="resetFilters">
        <q-icon name="restart_alt" />重置
      </button>
    </section>

    <div class="metric-grid">
      <article v-for="item in metrics" :key="item.label" class="metric-card tech-panel">
        <span class="metric-icon"><q-icon :name="item.icon" size="20px" /></span>
        <div>
          <span>{{ item.label }}</span
          ><strong
            >{{ item.value }}<small>{{ item.unit }}</small></strong
          >
        </div>
        <em :class="item.tone">{{ item.note }}</em>
      </article>
    </div>

    <section class="tech-panel daily-additions-panel">
      <div class="panel-heading daily-additions-heading">
        <div>
          <h2 class="panel-title"><q-icon name="event_note" />每日新增项目</h2>
          <p>按公告发布日期统计，点击日期查看当天新增的具体项目</p>
        </div>
        <span class="panel-meta">近 {{ dailyAdditionDays.length }} 个有新增的公告日</span>
      </div>
      <div v-if="dailyAdditionDays.length" class="daily-additions-body">
        <div class="daily-date-strip" role="tablist" aria-label="每日新增项目日期">
          <button
            v-for="day in dailyAdditionDays"
            :key="day.date"
            type="button"
            role="tab"
            :aria-selected="selectedDailyDate === day.date"
            :class="{ active: selectedDailyDate === day.date }"
            @click="selectedDailyDate = day.date"
          >
            <span>{{ day.shortDate }}</span>
            <strong>{{ day.count }}<small>项</small></strong>
            <em>{{ day.weekday }}</em>
          </button>
        </div>
        <div class="daily-projects">
          <div class="daily-projects-summary">
            <span
              ><b>{{ selectedDailyDateLabel }}</b
              >共新增</span
            >
            <strong>{{ selectedDailyProjects.length }} 个项目</strong>
          </div>
          <div class="daily-project-list">
            <button
              v-for="project in selectedDailyProjects"
              :key="project.id"
              type="button"
              class="daily-project-item"
              @click="selectedProject = project"
            >
              <span class="daily-project-rating" :class="`grade-${project.rating.toLowerCase()}`">{{
                project.rating || '—'
              }}</span>
              <span class="daily-project-name"
                ><strong>{{ project.name }}</strong
                ><small
                  >{{ project.province }} · {{ project.city || '地区待补充' }} ·
                  {{ project.category || '类型待补充' }}</small
                ></span
              >
              <span class="daily-project-amount"
                ><small>控制价/估算额</small><b>{{ amountLabel(project.amount) }}</b></span
              >
              <span class="daily-project-deadline"
                ><small>{{ project.openDate ? '开标时间' : '截止时间' }}</small
                ><b>{{ project.openDate || project.deadline || '待公布' }}</b></span
              >
              <q-icon name="chevron_right" />
            </button>
          </div>
        </div>
      </div>
      <div v-else class="daily-additions-empty">当前数据中没有可用的公告发布日期</div>
    </section>

    <div class="dashboard-grid">
      <aside class="tech-panel alert-panel">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="notifications_active" />开标/截止预警</h2>
          <span class="danger-count">{{ urgentProjects.length }}</span>
        </div>
        <div class="alert-list">
          <button
            v-for="project in pagedUrgentProjects"
            :key="project.id"
            type="button"
            class="alert-item"
            @click="selectedProject = project"
          >
            <span class="alert-days" :class="{ critical: project.days <= 3 }"
              >{{ project.days }}<small>{{ project.openDate ? '天开标' : '天截止' }}</small></span
            >
            <span class="alert-content"
              ><strong>{{ project.name }}</strong
              ><em>{{ project.city }} · {{ project.category }}</em></span
            >
            <b>{{ project.rating || '—' }}</b>
          </button>
        </div>
        <div v-if="urgentPageCount > 1" class="alert-pagination">
          <q-pagination
            v-model="urgentPage"
            :max="urgentPageCount"
            :max-pages="5"
            direction-links
            color="light-blue-5"
            active-color="light-blue-8"
            size="sm"
          />
          <span>{{ urgentPage }}/{{ urgentPageCount }}</span>
        </div>
        <div class="stage-summary">
          <div class="mini-heading">跟踪阶段分布</div>
          <div v-for="stage in stages" :key="stage.label" class="stage-row">
            <span>{{ stage.label }}</span
            ><i><b :style="{ width: `${stage.value}%` }" /></i><em>{{ stage.count }}</em>
          </div>
        </div>
      </aside>

      <section class="tech-panel map-panel">
        <div class="panel-heading map-heading">
          <div class="map-title-group">
            <button
              v-if="mapProvider === 'echarts' && mapLevel === 'province'"
              type="button"
              class="back-button"
              @click="resetMap"
            >
              <q-icon name="arrow_back" />全国
            </button>
            <h2 class="panel-title"><q-icon name="public" />{{ mapTitle }}</h2>
          </div>
          <div class="map-switches">
            <div class="map-provider">
              <button
                type="button"
                :class="{ active: mapProvider === 'echarts' }"
                @click="mapProvider = 'echarts'"
              >
                ECharts
              </button>
              <button
                type="button"
                :class="{ active: mapProvider === 'amap' }"
                @click="mapProvider = 'amap'"
              >
                高德 GIS
              </button>
            </div>
            <div class="map-modes">
              <button
                v-for="mode in mapModes"
                :key="mode.key"
                type="button"
                :class="{ active: mapMode === mode.key }"
                @click="mapMode = mode.key"
              >
                {{ mode.label }}
              </button>
            </div>
          </div>
        </div>
        <div class="map-body">
          <div v-show="mapProvider === 'echarts'" ref="mapElement" class="echarts-map" />
          <AmapProjectMap
            v-if="mapProvider === 'amap'"
            :projects="amapProjects"
            :display-mode="mapMode"
            @project-click="handleAmapProjectClick"
          />
          <div v-if="mapProvider === 'echarts'" class="map-legend">
            <span>低</span><i /><span>高</span>
          </div>
          <div v-if="mapProvider === 'echarts'" class="map-hint">
            <q-icon name="ads_click" />点击省份下钻，点击城市查看项目
          </div>
          <div class="map-mode-note">
            <q-icon :name="mapModeMeta.icon" />
            <span
              ><b>{{ mapModeMeta.label }}</b
              >{{ mapModeMeta.description }}</span
            >
          </div>
          <div v-if="mapMode === 'tracking' && !hasTrackedProjects" class="map-empty-note">
            当前项目尚未录入跟踪阶段，地图暂无跟踪深度数据
          </div>
          <div v-if="mapProvider === 'echarts' && selectedArea" class="area-card">
            <div class="area-card__head">
              <div>
                <span>当前区域</span><strong>{{ selectedArea }}</strong>
              </div>
              <button type="button" aria-label="关闭区域卡片" @click="clearArea">
                <q-icon name="close" />
              </button>
            </div>
            <div class="area-stats">
              <div>
                <span>项目总数</span><b>{{ areaStats.total }}</b>
              </div>
              <div>
                <span>在跟踪</span><b>{{ areaStats.tracked }}</b>
              </div>
              <div>
                <span>待开标</span><b class="danger">{{ areaStats.pending }}</b>
              </div>
              <div>
                <span>总造价</span><b>{{ amountLabel(areaStats.amount) }}</b>
              </div>
            </div>
            <button type="button" class="area-action" @click="scrollToLedger">
              查看区域项目卡片 <q-icon name="arrow_forward" />
            </button>
          </div>
        </div>
      </section>

      <aside class="tech-panel ranking-panel">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="leaderboard" />省份造价排行</h2>
          <span class="panel-meta">单位：元</span>
        </div>
        <div class="ranking-list">
          <div
            v-for="(province, index) in provinceRanking"
            :key="province.name"
            class="ranking-row"
          >
            <b :class="{ top: index < 3 }">{{ index + 1 }}</b>
            <div>
              <span>{{ province.name }}</span
              ><i><em :style="{ width: `${province.percent}%` }" /></i>
            </div>
            <strong>{{ yuanNumberLabel(province.amount) }}</strong>
          </div>
        </div>
        <div class="rating-block">
          <div class="mini-heading rating-heading">
            <span>ABCD 项目评级</span>
            <button type="button" class="rating-settings-button" @click="openRatingSettings">
              <q-icon name="tune" />评级规则
            </button>
          </div>
          <div class="rating-chart">
            <div class="rating-donut" :style="ratingDonutStyle">
              <span
                ><strong>{{ filteredProjects.length }}</strong
                ><small>筛选项目</small></span
              >
            </div>
            <div class="rating-legend">
              <div v-for="rating in ratingData" :key="rating.grade">
                <i :class="`grade-${rating.grade.toLowerCase()}`" /><span>{{ rating.grade }}级</span
                ><b>{{ rating.percent }}%</b>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <div class="lower-grid">
      <section class="tech-panel trend-panel">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="show_chart" />月度开标数量趋势</h2>
          <div class="chart-legend">
            <span><i />项目数量</span><span><i />重点项目</span>
          </div>
        </div>
        <div class="trend-chart">
          <div class="axis-labels">
            <span v-for="value in trendAxisLabels" :key="value">{{ value }}</span>
          </div>
          <svg viewBox="0 0 760 170" preserveAspectRatio="none" aria-label="月度开标趋势图">
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#168cff" stop-opacity=".36" />
                <stop offset="1" stop-color="#168cff" stop-opacity="0" />
              </linearGradient>
            </defs>
            <path :d="trendAreaPath" fill="url(#areaGradient)" />
            <polyline :points="trendProjectPoints" fill="none" stroke="#30c8ff" stroke-width="3" />
            <polyline
              :points="trendPriorityPoints"
              fill="none"
              stroke="#507cff"
              stroke-width="2"
              stroke-dasharray="5 5"
            />
          </svg>
          <div class="month-labels">
            <span v-for="month in monthlyTrend" :key="month.key">{{ month.label }}</span>
          </div>
        </div>
      </section>

      <section class="tech-panel opportunity-panel">
        <div class="panel-heading">
          <h2 class="panel-title"><q-icon name="tips_and_updates" />本周重点机会</h2>
          <span class="panel-meta">AI RECOMMENDATION</span>
        </div>
        <div class="opportunity-list">
          <button
            v-for="project in topOpportunities"
            :key="project.id"
            type="button"
            @click="selectedProject = project"
          >
            <span class="grade-badge">{{ project.rating || '—' }}</span>
            <span
              ><strong>{{ project.name }}</strong
              ><em>{{ project.owner }}</em></span
            >
            <b>{{ amountLabel(project.controlPrice) }}</b>
            <q-icon name="chevron_right" />
          </button>
        </div>
      </section>
    </div>

    <section ref="ledgerElement" class="tech-panel ledger-panel">
      <div class="panel-heading">
        <h2 class="panel-title"><q-icon name="table_view" />{{ ledgerTitle }}</h2>
        <span class="panel-meta"
          >共 {{ filteredProjects.length }} 条{{ ledgerRangeLabel }} · 当前显示
          {{ ledgerRangeStart }}–{{ ledgerRangeEnd }} 条</span
        >
      </div>
      <div class="ledger-scroll">
        <table>
          <thead>
            <tr>
              <th>评级</th>
              <th>项目名称</th>
              <th>工程类型</th>
              <th>所属地区</th>
              <th>业主单位</th>
              <th>公告日期</th>
              <th>开标/截止倒计时</th>
              <th>控制价</th>
              <th>预估合同额</th>
              <th>暂列金额</th>
              <th>开标日期</th>
              <th>投标截止日</th>
              <th>跟踪阶段</th>
              <th>责任人</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="project in pagedLedgerProjects"
              :key="project.id"
              @click="selectedProject = project"
            >
              <td>
                <span class="table-grade" :class="gradeClass(project.rating)">{{
                  project.rating || '—'
                }}</span>
              </td>
              <td>
                <strong>{{ project.name }}</strong>
              </td>
              <td>{{ project.category }}</td>
              <td>{{ locationLabel(project) }}</td>
              <td>{{ blankLabel(project.owner) }}</td>
              <td>{{ project.announcementDate || '—' }}</td>
              <td>
                <span :class="{ 'deadline-danger': project.days >= 0 && project.days <= 3 }">{{
                  countdownLabel(project)
                }}</span>
              </td>
              <td>{{ amountLabel(project.controlPrice) }}</td>
              <td>{{ amountLabel(project.estimatedContractAmount) }}</td>
              <td>{{ amountLabel(project.provisionalSum) }}</td>
              <td>{{ blankLabel(project.openDate) }}</td>
              <td>{{ blankLabel(project.deadline) }}</td>
              <td>
                <span class="stage-tag">{{ blankLabel(project.status) }}</span>
              </td>
              <td>{{ blankLabel(project.ownerPerson) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="ledger-pagination">
        <div class="ledger-page-size">
          <span>每页显示</span>
          <select v-model.number="ledgerPageSize" aria-label="每页显示项目数量">
            <option v-for="size in ledgerPageSizeOptions" :key="size" :value="size">
              {{ size }} 条
            </option>
          </select>
        </div>
        <q-pagination
          v-model="ledgerPage"
          :max="ledgerPageCount"
          :max-pages="7"
          boundary-links
          direction-links
          color="light-blue-5"
          active-color="light-blue-8"
          size="sm"
        />
        <span>第 {{ ledgerPage }}/{{ ledgerPageCount }} 页</span>
      </div>
    </section>

    <div v-if="showRatingSettings" class="project-overlay" @click.self="closeRatingSettings">
      <article class="rating-dialog tech-panel">
        <div class="dialog-head">
          <div>
            <q-icon name="tune" size="24px" />
            <div>
              <small>RATING POLICY</small>
              <h2>ABCD 评级规则</h2>
            </div>
          </div>
          <button type="button" aria-label="关闭评级规则" @click="closeRatingSettings">
            <q-icon name="close" />
          </button>
        </div>
        <p class="rating-dialog__intro">
          系统根据项目金额、截止紧迫度和信息完整度计算基础分；你也可以调整各等级的最低分值，保存后立即按新规则重新评级。
        </p>
        <div class="rating-mode-switch">
          <button
            type="button"
            :class="{ active: ratingDraft.mode === 'system' }"
            @click="ratingDraft.mode = 'system'"
          >
            系统默认
          </button>
          <button
            type="button"
            :class="{ active: ratingDraft.mode === 'custom' }"
            @click="ratingDraft.mode = 'custom'"
          >
            自定义规则
          </button>
        </div>
        <div class="rating-threshold-grid" :class="{ disabled: ratingDraft.mode === 'system' }">
          <label
            ><span>A级最低分</span
            ><input
              v-model.number="ratingDraft.aMin"
              type="number"
              min="1"
              max="100"
              :disabled="ratingDraft.mode === 'system'"
          /></label>
          <label
            ><span>B级最低分</span
            ><input
              v-model.number="ratingDraft.bMin"
              type="number"
              min="1"
              max="99"
              :disabled="ratingDraft.mode === 'system'"
          /></label>
          <label
            ><span>C级最低分</span
            ><input
              v-model.number="ratingDraft.cMin"
              type="number"
              min="1"
              max="98"
              :disabled="ratingDraft.mode === 'system'"
          /></label>
          <div><span>D级</span><strong>低于 C 级最低分</strong></div>
        </div>
        <div class="rating-score-help">
          <b>系统计分构成</b><span>项目金额 40分</span><span>截止紧迫度 30分</span
          ><span>业主、类型、城市完整度各10分</span>
        </div>
        <p v-if="ratingRuleError" class="rating-rule-error">{{ ratingRuleError }}</p>
        <div class="dialog-actions">
          <button type="button" class="secondary-action" @click="restoreDefaultRatingRule">
            恢复默认
          </button>
          <button type="button" @click="saveRatingSettings">保存并重新评级</button>
        </div>
      </article>
    </div>

    <div v-if="showAiRating" class="project-overlay" @click.self="closeAiRatingAssistant">
      <article class="ai-rating-dialog tech-panel">
        <div class="dialog-head">
          <div>
            <q-icon name="psychology" size="26px" />
            <div>
              <small>AI PROJECT RATING</small>
              <h2>AI项目评级助手</h2>
            </div>
          </div>
          <button
            type="button"
            aria-label="关闭AI评级助手"
            :disabled="aiRatingLoading || aiRatingApplying"
            @click="closeAiRatingAssistant"
          >
            <q-icon name="close" />
          </button>
        </div>
        <div class="ai-rating-intro">
          <q-icon name="auto_awesome" />
          <span
            >用自然语言描述A、B、C、D四级标准。模型会结合模块1中的项目金额、地区、类型、业主、公告及开标时间逐项评级；确认前不会修改数据库。</span
          >
        </div>
        <div class="ai-rating-scope">
          <span>评级范围</span>
          <button
            type="button"
            :class="{ active: aiRatingScope === 'filtered' }"
            :disabled="aiRatingLoading"
            @click="aiRatingScope = 'filtered'"
          >
            当前筛选项目（{{ filteredProjects.length }}项）
          </button>
          <button
            type="button"
            :class="{ active: aiRatingScope === 'all' }"
            :disabled="aiRatingLoading"
            @click="aiRatingScope = 'all'"
          >
            全部项目（{{ allProjects.length }}项）
          </button>
        </div>
        <label class="ai-rating-criteria">
          <span>ABCD评级标准</span>
          <textarea
            v-model.trim="aiRatingCriteria"
            rows="8"
            :disabled="aiRatingLoading || aiRatingApplying"
            placeholder="例如：A级为控制价5000万元以上、业主明确且30天内开标的重点项目；B级……"
          ></textarea>
          <small
            >标准越明确，结果越稳定。建议分别写清四个等级，并说明金额、时间、地区和项目类型的优先级。</small
          >
        </label>
        <p v-if="aiRatingError" class="ai-rating-message error">
          <q-icon name="error_outline" />{{ aiRatingError }}
        </p>
        <p v-if="aiRatingSuccess" class="ai-rating-message success">
          <q-icon name="check_circle" />{{ aiRatingSuccess }}
        </p>
        <div v-if="aiRatingPreview.length" class="ai-rating-preview">
          <div class="ai-rating-summary">
            <span>模型：{{ aiRatingModel || '已配置模型' }}</span>
            <div>
              <b
                v-for="grade in aiRatingGradeCounts"
                :key="grade.grade"
                :class="`grade-${grade.grade.toLowerCase()}`"
                >{{ grade.grade }}级 {{ grade.count }}</b
              >
            </div>
            <strong>{{ aiRatingChangedCount }}项评级将发生变化</strong>
          </div>
          <div class="ai-rating-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>项目</th>
                  <th>原评级</th>
                  <th>AI评级</th>
                  <th>评级依据</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in aiRatingPreview" :key="item.id">
                  <td>{{ item.name }}</td>
                  <td>
                    <span class="table-grade" :class="gradeClass(item.previousRating)">{{
                      item.previousRating || '—'
                    }}</span>
                  </td>
                  <td>
                    <span class="table-grade" :class="gradeClass(item.rating)">{{
                      item.rating
                    }}</span>
                  </td>
                  <td>{{ item.reason || '模型未提供说明' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="dialog-actions ai-rating-actions">
          <button
            type="button"
            class="secondary-action"
            :disabled="aiRatingLoading || aiRatingApplying"
            @click="closeAiRatingAssistant"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="aiRatingLoading || aiRatingApplying || aiRatingCriteria.length < 10"
            @click="generateAiRatingPreview"
          >
            <q-icon name="auto_awesome" />{{
              aiRatingLoading
                ? 'AI正在分批评级…'
                : aiRatingPreview.length
                  ? '重新生成预览'
                  : '生成评级预览'
            }}
          </button>
          <button
            type="button"
            class="apply-ai-rating"
            :disabled="!aiRatingPreview.length || aiRatingLoading || aiRatingApplying"
            @click="applyAiRatings"
          >
            <q-icon name="published_with_changes" />{{
              aiRatingApplying ? '正在写入…' : '确认并应用评级'
            }}
          </button>
        </div>
      </article>
    </div>

    <div v-if="selectedCity" class="project-overlay" @click.self="closeCityProjects">
      <article class="city-project-dialog tech-panel">
        <div class="dialog-head">
          <div>
            <q-icon name="location_city" size="24px" />
            <div>
              <small>CITY PROJECTS</small>
              <h2>{{ selectedCity }}项目卡片</h2>
            </div>
          </div>
          <button type="button" aria-label="关闭城市项目卡片" @click="closeCityProjects">
            <q-icon name="close" />
          </button>
        </div>
        <div class="city-project-summary">
          共 {{ selectedCityProjects.length }} 个项目 · 数据来自当前数据库筛选结果
        </div>
        <div v-if="selectedCityProjects.length" class="city-project-grid">
          <button
            v-for="project in selectedCityProjects"
            :key="project.id"
            type="button"
            class="city-project-card"
            @click="openProjectFromCity(project)"
          >
            <span class="table-grade" :class="gradeClass(project.rating)">{{
              project.rating || '—'
            }}</span>
            <div>
              <strong>{{ project.name }}</strong
              ><small>{{ project.category }} · {{ project.district || project.city }}</small>
            </div>
            <dl>
              <div>
                <dt>业主单位</dt>
                <dd>{{ blankLabel(project.owner) }}</dd>
              </div>
              <div>
                <dt>开标/截止</dt>
                <dd>{{ project.openDate || project.deadline || '—' }}</dd>
              </div>
              <div>
                <dt>项目金额</dt>
                <dd>{{ amountLabel(project.amount) }}</dd>
              </div>
            </dl>
          </button>
        </div>
        <div v-else class="history-empty">当前筛选条件下该城市暂无项目</div>
      </article>
    </div>

    <div v-if="showUpdateHistory" class="project-overlay" @click.self="showUpdateHistory = false">
      <article class="history-dialog tech-panel">
        <div class="dialog-head history-dialog__head">
          <div>
            <q-icon name="history" size="24px" />
            <div>
              <small>DATA SYNC HISTORY</small>
              <h2>项目数据同步记录</h2>
            </div>
          </div>
          <button type="button" aria-label="关闭更新记录" @click="showUpdateHistory = false">
            <q-icon name="close" />
          </button>
        </div>
        <div v-if="historyLoading" class="history-empty">正在读取更新记录…</div>
        <div v-else-if="historyError" class="history-empty history-empty--error">
          {{ historyError }}
        </div>
        <div v-else-if="!updateHistory.length" class="history-empty">暂无更新记录</div>
        <div v-else class="history-list">
          <div
            v-for="(record, index) in pagedUpdateHistory"
            :key="`${record.updatedAt}-${index}`"
            class="history-item"
          >
            <i :class="{ failed: !record.success }"
              ><q-icon :name="record.success ? 'check' : 'close'"
            /></i>
            <div class="history-item__main">
              <strong>{{ record.success ? '招标项目更新成功' : '招标项目更新失败' }}</strong>
              <span>{{ record.updatedAt }}</span>
              <small>{{ record.source }}</small>
              <p v-if="record.message">{{ record.message }}</p>
            </div>
            <div class="history-item__stats">
              <span
                >在招项目<strong>{{
                  record.opportunityCount ?? record.projectCount ?? 0
                }}</strong></span
              >
              <span
                >本次新增<strong class="added">+{{ record.addedCount }}</strong></span
              >
            </div>
          </div>
          <div v-if="historyPageCount > 1" class="history-pagination">
            <button type="button" :disabled="historyPage <= 1" @click="historyPage--">
              <q-icon name="chevron_left" />上一页
            </button>
            <span
              >第 {{ historyPage }} / {{ historyPageCount }} 页 · 近7天共
              {{ updateHistory.length }} 条</span
            >
            <button
              type="button"
              :disabled="historyPage >= historyPageCount"
              @click="historyPage++"
            >
              下一页<q-icon name="chevron_right" />
            </button>
          </div>
        </div>
      </article>
    </div>

    <div v-if="selectedProject" class="project-overlay" @click.self="selectedProject = null">
      <article class="project-dialog tech-panel">
        <div class="dialog-head">
          <div>
            <span class="table-grade" :class="gradeClass(selectedProject.rating)">{{
              selectedProject.rating || '—'
            }}</span>
            <div>
              <small>项目详情</small>
              <h2>{{ selectedProject.name }}</h2>
            </div>
          </div>
          <button type="button" aria-label="关闭项目详情" @click="selectedProject = null">
            <q-icon name="close" />
          </button>
        </div>
        <div class="dialog-grid">
          <div>
            <span>工程类型</span><strong>{{ selectedProject.category }}</strong>
          </div>
          <div>
            <span>所属省市</span><strong>{{ locationLabel(selectedProject) }}</strong>
          </div>
          <div>
            <span>业主单位</span><strong>{{ blankLabel(selectedProject.owner) }}</strong>
          </div>
          <div>
            <span>招标控制价</span><strong>{{ amountLabel(selectedProject.controlPrice) }}</strong>
          </div>
          <div>
            <span>公告发布日期</span><strong>{{ selectedProject.announcementDate || '—' }}</strong>
          </div>
          <div>
            <span>预估合同额</span
            ><strong>{{ amountLabel(selectedProject.estimatedContractAmount) }}</strong>
          </div>
          <div>
            <span>暂列金额</span><strong>{{ amountLabel(selectedProject.provisionalSum) }}</strong>
          </div>
          <div>
            <span>开标日期</span><strong>{{ blankLabel(selectedProject.openDate) }}</strong>
          </div>
          <div>
            <span>投标截止日</span><strong>{{ blankLabel(selectedProject.deadline) }}</strong>
          </div>
          <div>
            <span>跟踪阶段</span><strong>{{ blankLabel(selectedProject.status) }}</strong>
          </div>
          <div>
            <span>跟进责任人</span><strong>{{ blankLabel(selectedProject.ownerPerson) }}</strong>
          </div>
        </div>
        <div class="dialog-section">
          <span>竞争对手</span>
          <p>{{ blankLabel(selectedProject.competitors) }}</p>
        </div>
        <div class="dialog-section">
          <span>最新跟进日志</span>
          <p>{{ blankLabel(selectedProject.log) }}</p>
        </div>
        <div v-if="selectedProject.sourceUrl" class="dialog-section">
          <span>数据来源</span>
          <p>
            {{ selectedProject.sourceName || '公开招标公告' }} ·
            <a :href="selectedProject.sourceUrl" target="_blank" rel="noopener noreferrer"
              >查看原始公告</a
            >
          </p>
        </div>
        <div class="dialog-actions">
          <button type="button" @click="openTrackingEditor(selectedProject)">更新跟进记录</button>
          <a
            v-if="selectedProject.sourceUrl"
            class="button-link"
            :href="selectedProject.sourceUrl"
            target="_blank"
            rel="noopener noreferrer"
            >查看招标公告</a
          >
        </div>
      </article>
    </div>

    <div v-if="trackingProject" class="project-overlay" @click.self="closeTrackingEditor">
      <article class="project-dialog tracking-dialog">
        <div class="dialog-head">
          <div>
            <q-icon name="edit_note" />
            <div>
              <small>PROJECT FOLLOW-UP</small>
              <h2>录入项目跟进</h2>
            </div>
          </div>
          <button type="button" aria-label="关闭跟进录入" @click="closeTrackingEditor">
            <q-icon name="close" />
          </button>
        </div>
        <p class="tracking-project-name">{{ trackingProject.name }}</p>
        <div class="tracking-form-grid">
          <label
            ><span>跟踪阶段 *</span
            ><select v-model="trackingForm.stage">
              <option v-for="stage in trackingStages" :key="stage" :value="stage">
                {{ stage }}
              </option>
            </select></label
          >
          <label
            ><span>跟进责任人</span
            ><input
              v-model.trim="trackingForm.responsiblePerson"
              maxlength="100"
              placeholder="请输入姓名"
          /></label>
          <label class="tracking-form-wide"
            ><span>竞争对手</span
            ><input
              v-model.trim="trackingForm.competitors"
              placeholder="多个单位可用顿号或逗号分隔"
          /></label>
          <label class="tracking-form-wide"
            ><span>本次跟进记录 *</span
            ><textarea
              v-model.trim="trackingForm.log"
              rows="4"
              maxlength="2000"
              placeholder="记录沟通结果、当前进展、待办事项等"
            ></textarea>
          </label>
          <label
            ><span>下次跟进时间</span
            ><input v-model="trackingForm.nextFollowUpAt" type="datetime-local"
          /></label>
        </div>
        <p v-if="trackingError" class="tracking-message tracking-message--error">
          {{ trackingError }}
        </p>
        <p v-if="trackingSuccess" class="tracking-message tracking-message--success">
          {{ trackingSuccess }}
        </p>
        <section class="tracking-history">
          <h3>历史跟进记录</h3>
          <p v-if="trackingLoading" class="tracking-history-empty">正在读取…</p>
          <p v-else-if="!trackingHistory.length" class="tracking-history-empty">暂无跟进记录</p>
          <article v-for="item in trackingHistory" :key="item.id">
            <header>
              <strong>{{ item.stage }}</strong
              ><time>{{ formatTrackingTime(item.createdAt) }}</time>
            </header>
            <p>{{ item.log }}</p>
            <small
              >{{ item.responsiblePerson || '未指定责任人'
              }}<template v-if="item.competitors">
                · 竞争对手：{{ item.competitors }}</template
              ></small
            >
          </article>
        </section>
        <div class="dialog-actions">
          <button type="button" class="button-secondary" @click="closeTrackingEditor">取消</button>
          <button type="button" :disabled="trackingSaving" @click="saveTrackingRecord">
            {{ trackingSaving ? '保存中…' : '保存跟进记录' }}
          </button>
        </div>
      </article>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import AmapProjectMap from '../components/AmapProjectMap.vue';
import { MapChart } from 'echarts/charts';
import { GeoComponent, TooltipComponent, VisualMapComponent } from 'echarts/components';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import type { AmapProjectPoint } from '../types/map';
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';

echarts.use([MapChart, GeoComponent, TooltipComponent, VisualMapComponent, CanvasRenderer]);

type MapMode = 'count' | 'tracking' | 'rating';
type MapLevel = 'country' | 'province';
type MapProvider = 'echarts' | 'amap';
type ProjectRating = 'A' | 'B' | 'C' | 'D' | '';

interface Project {
  dbId?: number;
  id: number;
  name: string;
  category: string;
  province: string;
  city: string;
  district?: string;
  lng: number;
  lat: number;
  owner: string;
  announcementDate?: string;
  days: number;
  amount: number;
  controlPrice?: number | null;
  estimatedContractAmount?: number | null;
  provisionalSum?: number | null;
  rating: ProjectRating;
  status: string;
  ownerPerson: string;
  openDate: string;
  deadline: string;
  competitors: string;
  log: string;
  sourceName?: string;
  sourceUrl?: string;
  projectCode?: string;
  sectionCode?: string;
  nextFollowUpAt?: string;
  locationPrecision?: string;
  aiRatingReason?: string;
  aiRatingCriteria?: string;
  aiRatedAt?: string;
}

interface AiRatingPreviewItem {
  id: number;
  name: string;
  previousRating: ProjectRating;
  rating: Exclude<ProjectRating, ''>;
  reason: string;
}

interface TrackingHistoryItem {
  id: number;
  projectId: number;
  stage: string;
  responsiblePerson: string;
  competitors: string;
  log: string;
  nextFollowUpAt: string;
  createdAt: string;
}

interface UpdateHistoryRecord {
  success: boolean;
  updatedAt: string;
  projectCount?: number;
  opportunityCount?: number;
  addedCount: number;
  source: string;
  message?: string;
}

interface ProvinceDatum {
  name: string;
  adcode: string;
  count: number;
  tracked: number;
  pending: number;
  amount: number;
  rating: number;
}

interface GeoFeature {
  properties?: { name?: string; adcode?: string | number };
}
interface GeoJson {
  features?: GeoFeature[];
}

const mapElement = ref<HTMLDivElement | null>(null);
const ledgerElement = ref<HTMLElement | null>(null);
const mapProvider = ref<MapProvider>('echarts');
const mapMode = ref<MapMode>('count');
const mapLevel = ref<MapLevel>('country');
const activeMapName = ref('china');
const selectedProvince = ref<ProvinceDatum | null>(null);
const selectedCity = ref('');
const selectedProject = ref<Project | null>(null);
const trackingProject = ref<Project | null>(null);
const trackingHistory = ref<TrackingHistoryItem[]>([]);
const trackingLoading = ref(false);
const trackingSaving = ref(false);
const trackingError = ref('');
const trackingSuccess = ref('');
const trackingStages = ['线索阶段', '初步对接', '资审报名', '标书编制', '已递交', '已开标'];
const trackingForm = reactive({
  stage: '线索阶段',
  responsiblePerson: '',
  competitors: '',
  log: '',
  nextFollowUpAt: '',
});
const showRatingSettings = ref(false);
const ratingRuleError = ref('');
const showAiRating = ref(false);
const aiRatingScope = ref<'filtered' | 'all'>('filtered');
const aiRatingCriteria = ref(
  'A级：战略重点项目，金额大、业主明确、近期具备投标条件；\nB级：综合条件较好，具有较高跟进价值；\nC级：条件一般或关键信息不完整，需要继续观察；\nD级：金额较小、时间不合适或当前参与价值较低。',
);
const aiRatingLoading = ref(false);
const aiRatingApplying = ref(false);
const aiRatingError = ref('');
const aiRatingSuccess = ref('');
const aiRatingModel = ref('');
const aiRatingPreview = ref<AiRatingPreviewItem[]>([]);
const aiRatingGradeCounts = computed(() =>
  ['A', 'B', 'C', 'D'].map((grade) => ({
    grade,
    count: aiRatingPreview.value.filter((item) => item.rating === grade).length,
  })),
);
const aiRatingChangedCount = computed(
  () => aiRatingPreview.value.filter((item) => item.rating !== item.previousRating).length,
);
const showUpdateHistory = ref(false);
const historyLoading = ref(false);
const historyError = ref('');
const updateHistory = ref<UpdateHistoryRecord[]>([]);
const historyPage = ref(1);
const historyPageSize = 5;
const historyPageCount = computed(() =>
  Math.max(1, Math.ceil(updateHistory.value.length / historyPageSize)),
);
const pagedUpdateHistory = computed(() => {
  const start = (historyPage.value - 1) * historyPageSize;
  return updateHistory.value.slice(start, start + historyPageSize);
});
let mapChart: echarts.ECharts | null = null;
let resizeObserver: ResizeObserver | null = null;

interface RatingRule {
  mode: 'system' | 'custom';
  aMin: number;
  bMin: number;
  cMin: number;
}

const defaultRatingRule: RatingRule = { mode: 'system', aMin: 76, bMin: 61, cMin: 41 };
const storedRatingRule = localStorage.getItem('bidding-rating-rule');
function parseStoredRatingRule(value: string | null): Partial<RatingRule> {
  if (!value) return {};
  try {
    return JSON.parse(value) as Partial<RatingRule>;
  } catch {
    return {};
  }
}
const ratingRule = ref<RatingRule>({
  ...defaultRatingRule,
  ...parseStoredRatingRule(storedRatingRule),
});
const ratingDraft = reactive<RatingRule>({ ...ratingRule.value });

const createDefaultFilters = () => ({
  keyword: '',
  scope: 'opportunity',
  category: '全部',
  opening: '全部',
  rating: '全部',
  status: '全部',
});
const filters = ref(createDefaultFilters());
const appliedFilters = ref(createDefaultFilters());
const filtersDirty = computed(
  () => JSON.stringify(filters.value) !== JSON.stringify(appliedFilters.value),
);
const scopeOptions = [
  { label: '在招项目', value: 'opportunity' },
  { label: '全部项目（含历史）', value: 'all' },
];
const openingOptions = [
  { label: '全部时段', value: '全部' },
  ...['7天内', '30天内', '本季度'].map((value) => ({ label: value, value })),
];
const ratingOptions = [
  { label: '全部评级', value: '全部' },
  ...['A', 'B', 'C', 'D'].map((value) => ({ label: value, value })),
];
const statusOptions = [
  { label: '全部状态', value: '全部' },
  ...['线索阶段', '初步对接', '资审报名', '标书编制', '已递交', '已开标'].map((value) => ({
    label: value,
    value,
  })),
];
const mapModes: { key: MapMode; label: string }[] = [
  { key: 'count', label: '项目数量' },
  { key: 'tracking', label: '跟踪深度' },
  { key: 'rating', label: 'ABCD评级' },
];
const mapModeMeta = computed(
  () =>
    ({
      count: { label: '项目数量：', description: '颜色越亮，区域内项目越多', icon: 'dataset' },
      tracking: {
        label: '跟踪深度：',
        description: '展示已进入业务跟踪流程的项目数量',
        icon: 'timeline',
      },
      rating: { label: 'ABCD评级：', description: '按区域项目平均评级分值着色', icon: 'grade' },
    })[mapMode.value],
);

const provinces = reactive<ProvinceDatum[]>([]);

const demoProjects: Project[] = [
  {
    id: 1,
    name: '滨海新区综合产业园总承包工程',
    category: '房建工程',
    province: '广东省',
    city: '深圳市',
    lng: 114.057868,
    lat: 22.543099,
    owner: '深圳产业投资集团',
    days: 2,
    amount: 12.8,
    rating: 'A',
    status: '标书编制',
    ownerPerson: '张明',
    openDate: '2026-10-23',
    deadline: '2026-10-22',
    competitors: '中建集团、华南建设、城投建设',
    log: '已完成技术方案二审，商务报价等待最终确认。',
  },
  {
    id: 2,
    name: '城市快速路改扩建工程一期',
    category: '市政工程',
    province: '江苏省',
    city: '南京市',
    lng: 118.796877,
    lat: 32.060255,
    owner: '南京城市建设发展有限公司',
    days: 3,
    amount: 8.6,
    rating: 'A',
    status: '已递交',
    ownerPerson: '李雪',
    openDate: '2026-10-24',
    deadline: '2026-10-23',
    competitors: '中交集团、江苏路桥',
    log: '投标文件已递交，等待开标。',
  },
  {
    id: 3,
    name: '智慧物流枢纽基础设施项目',
    category: '房建工程',
    province: '浙江省',
    city: '杭州市',
    lng: 120.15507,
    lat: 30.274084,
    owner: '浙江智慧物流有限公司',
    days: 6,
    amount: 6.3,
    rating: 'B',
    status: '标书编制',
    ownerPerson: '王晨',
    openDate: '2026-10-27',
    deadline: '2026-10-26',
    competitors: '浙江建工、杭州城建',
    log: '已与业主完成第二轮技术交流。',
  },
  {
    id: 4,
    name: '省道综合提升改造工程',
    category: '公路工程',
    province: '山东省',
    city: '济南市',
    lng: 117.120128,
    lat: 36.652069,
    owner: '山东交通发展集团',
    days: 9,
    amount: 5.7,
    rating: 'B',
    status: '资审报名',
    ownerPerson: '赵峰',
    openDate: '2026-10-30',
    deadline: '2026-10-28',
    competitors: '山东路桥、中铁十四局',
    log: '资格预审材料准备完成80%。',
  },
  {
    id: 5,
    name: '区域水环境综合治理项目',
    category: '水利工程',
    province: '四川省',
    city: '成都市',
    lng: 104.066541,
    lat: 30.572269,
    owner: '成都水务投资集团',
    days: 12,
    amount: 9.2,
    rating: 'A',
    status: '初步对接',
    ownerPerson: '陈欣',
    openDate: '2026-11-02',
    deadline: '2026-10-31',
    competitors: '中国水电、四川水建',
    log: '已获取初步设计资料，正在测算施工成本。',
  },
  {
    id: 6,
    name: '高新区科创中心建设项目',
    category: '房建工程',
    province: '湖北省',
    city: '武汉市',
    lng: 114.305393,
    lat: 30.593099,
    owner: '武汉高科集团',
    days: 18,
    amount: 4.8,
    rating: 'B',
    status: '线索阶段',
    ownerPerson: '刘洋',
    openDate: '2026-11-08',
    deadline: '2026-11-06',
    competitors: '中建三局、武汉建工',
    log: '正在核实招标计划与资金到位情况。',
  },
  {
    id: 7,
    name: '轨道交通配套市政工程',
    category: '市政工程',
    province: '河南省',
    city: '郑州市',
    lng: 113.625368,
    lat: 34.746599,
    owner: '郑州轨道交通集团',
    days: 24,
    amount: 7.5,
    rating: 'C',
    status: '初步对接',
    ownerPerson: '周林',
    openDate: '2026-11-14',
    deadline: '2026-11-12',
    competitors: '中铁工程、中交一公局',
    log: '竞争激烈，持续评估参与价值。',
  },
  {
    id: 8,
    name: '沿海防洪能力提升工程',
    category: '水利工程',
    province: '福建省',
    city: '厦门市',
    lng: 118.089425,
    lat: 24.479834,
    owner: '厦门市政集团',
    days: 30,
    amount: 3.9,
    rating: 'C',
    status: '线索阶段',
    ownerPerson: '徐静',
    openDate: '2026-11-20',
    deadline: '2026-11-18',
    competitors: '福建水利、中国水电',
    log: '已录入项目线索，等待公告正式发布。',
  },
];

const allProjects = ref<Project[]>([]);
const selectedDailyDate = ref('');
function announcementDateKey(value?: string): string {
  return value?.trim().slice(0, 10) ?? '';
}
function dailyDateParts(value: string): { shortDate: string; weekday: string } {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return { shortDate: value, weekday: '' };
  return {
    shortDate: `${date.getMonth() + 1}月${date.getDate()}日`,
    weekday: new Intl.DateTimeFormat('zh-CN', { weekday: 'short' }).format(date),
  };
}
const dailyAdditionDays = computed(() => {
  const counts = new Map<string, number>();
  for (const project of allProjects.value) {
    const date = announcementDateKey(project.announcementDate);
    if (date) counts.set(date, (counts.get(date) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .slice(0, 7)
    .map(([date, count]) => ({ date, count, ...dailyDateParts(date) }));
});
const selectedDailyProjects = computed(() =>
  allProjects.value
    .filter((project) => announcementDateKey(project.announcementDate) === selectedDailyDate.value)
    .sort((left, right) => right.id - left.id),
);
const selectedDailyDateLabel = computed(() =>
  selectedDailyDate.value ? `${dailyDateParts(selectedDailyDate.value).shortDate} ` : '',
);
watch(
  dailyAdditionDays,
  (days) => {
    if (!days.length) {
      selectedDailyDate.value = '';
      return;
    }
    if (!days.some((day) => day.date === selectedDailyDate.value))
      selectedDailyDate.value = days[0]!.date;
  },
  { immediate: true },
);
const categoryOptions = computed(() => [
  { label: '全部类别', value: '全部' },
  ...Array.from(new Set(allProjects.value.map((project) => project.category)))
    .sort((left, right) => left.localeCompare(right, 'zh-CN'))
    .map((value) => ({ label: value, value })),
]);
const dataSourceMode = ref<'live' | 'demo' | 'error'>('demo');
const dataUpdatedAt = ref('');
const projectApiUrl = import.meta.env.QCLI_PROJECT_API_URL?.trim() ?? '';
let projectRefreshTimer: ReturnType<typeof setInterval> | undefined;
const dataSourceLabel = computed(() => {
  if (dataSourceMode.value === 'live')
    return dataUpdatedAt.value
      ? `数据服务正常 · 同步于 ${dataUpdatedAt.value}`
      : '数据服务正常 · 已连接';
  if (dataSourceMode.value === 'error') return '数据服务异常 · 已切换本地数据';
  return '本地演示数据 · 待接入数据服务';
});

const closedProjectStatuses = new Set(['已开标', '已中标', '未中标', '废标', '流标', '已终止']);
function isOpportunityProject(project: Project): boolean {
  const deadlineUnknown = !project.openDate && !project.deadline;
  return (project.days >= 0 || deadlineUnknown) && !closedProjectStatuses.has(project.status);
}

const opportunityProjects = computed(() => allProjects.value.filter(isOpportunityProject));
const hasTrackedProjects = computed(() =>
  filteredProjects.value.some(
    (project) => Boolean(project.status) && project.status !== '线索阶段',
  ),
);
const filteredProjects = computed(() =>
  allProjects.value.filter((project) => {
    const scopeMatch =
      appliedFilters.value.scope === 'all' ||
      (appliedFilters.value.scope === 'opportunity' && isOpportunityProject(project));
    const keyword = appliedFilters.value.keyword.toLowerCase();
    const keywordMatch =
      !keyword ||
      `${project.name}${project.category}${project.province}${project.city}${project.owner}${project.ownerPerson}${project.announcementDate ?? ''}${project.openDate}${project.deadline}`
        .toLowerCase()
        .includes(keyword);
    const categoryMatch =
      appliedFilters.value.category === '全部' ||
      project.category === appliedFilters.value.category;
    const ratingMatch =
      appliedFilters.value.rating === '全部' || project.rating === appliedFilters.value.rating;
    const statusMatch =
      appliedFilters.value.status === '全部' || project.status === appliedFilters.value.status;
    const openingDate = project.openDate || project.deadline;
    const openingAt = openingDate ? new Date(openingDate.replace(' ', 'T')) : null;
    const now = new Date();
    const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3;
    const quarterStart = new Date(now.getFullYear(), quarterStartMonth, 1);
    const quarterEnd = new Date(now.getFullYear(), quarterStartMonth + 3, 1);
    const openingMatch =
      appliedFilters.value.opening === '全部' ||
      (appliedFilters.value.opening === '7天内' && project.days >= 0 && project.days <= 7) ||
      (appliedFilters.value.opening === '30天内' && project.days >= 0 && project.days <= 30) ||
      (appliedFilters.value.opening === '本季度' &&
        openingAt !== null &&
        !Number.isNaN(openingAt.getTime()) &&
        openingAt >= quarterStart &&
        openingAt < quarterEnd);
    return (
      scopeMatch && keywordMatch && categoryMatch && ratingMatch && statusMatch && openingMatch
    );
  }),
);
const ledgerPageSizeOptions = [10, 15, 20, 50];
const ledgerPageSize = ref(15);
const ledgerPage = ref(1);
function projectDateTimestamp(value?: string): number {
  if (!value) return Number.NEGATIVE_INFINITY;
  const timestamp = new Date(value.replace(' ', 'T')).getTime();
  return Number.isNaN(timestamp) ? Number.NEGATIVE_INFINITY : timestamp;
}
const ledgerProjects = computed(() => {
  if (appliedFilters.value.scope !== 'all') return filteredProjects.value;
  return [...filteredProjects.value].sort((left, right) => {
    const publishDifference =
      projectDateTimestamp(right.announcementDate) - projectDateTimestamp(left.announcementDate);
    if (publishDifference) return publishDifference;
    const deadlineDifference =
      projectDateTimestamp(right.deadline || right.openDate) -
      projectDateTimestamp(left.deadline || left.openDate);
    return deadlineDifference || right.id - left.id;
  });
});
const ledgerPageCount = computed(() =>
  Math.max(1, Math.ceil(ledgerProjects.value.length / ledgerPageSize.value)),
);
const ledgerRangeStart = computed(() =>
  ledgerProjects.value.length ? (ledgerPage.value - 1) * ledgerPageSize.value + 1 : 0,
);
const ledgerRangeEnd = computed(() =>
  Math.min(ledgerPage.value * ledgerPageSize.value, ledgerProjects.value.length),
);
const pagedLedgerProjects = computed(() => {
  const start = (ledgerPage.value - 1) * ledgerPageSize.value;
  return ledgerProjects.value.slice(start, start + ledgerPageSize.value);
});
watch(ledgerPageSize, () => {
  ledgerPage.value = 1;
});
watch(ledgerPageCount, (pageCount) => {
  if (ledgerPage.value > pageCount) ledgerPage.value = pageCount;
});
const ledgerTitle = computed(() =>
  appliedFilters.value.scope === 'opportunity' ? '在招项目台账' : '全部项目台账',
);
const ledgerRangeLabel = computed(() =>
  appliedFilters.value.scope === 'opportunity' ? '在招项目' : '项目（含历史）',
);

const metrics = computed(() => {
  const projects = filteredProjects.value;
  const closingSoon = projects.filter((project) => {
    const days = daysUntil(project.deadline);
    return days >= 0 && days <= 7;
  }).length;
  const pending = projects.filter((project) => project.days >= 0 && project.days <= 30).length;
  const totalAmount = projects.reduce((sum, project) => sum + project.amount, 0);
  const provinceCount = new Set(projects.map((project) => project.province)).size;
  const aCount = projects.filter((project) => project.rating === 'A').length;
  const aPercent = projects.length ? Math.round((aCount / projects.length) * 100) : 0;
  return [
    {
      label: appliedFilters.value.scope === 'all' ? '全部项目' : '在招项目',
      value: String(projects.length),
      unit: '项',
      note: `覆盖 ${provinceCount} 个省份`,
      tone: 'positive',
      icon: 'dataset',
    },
    {
      label: '7天内投标截止',
      value: String(closingSoon),
      unit: '项',
      note: '优先完成报名与递交',
      tone: closingSoon ? 'danger' : 'info',
      icon: 'event_busy',
    },
    {
      label: '30天内待开标',
      value: String(pending),
      unit: '项',
      note: `${projects.filter((project) => project.days >= 0 && project.days <= 3).length}项临近截止`,
      tone: 'danger',
      icon: 'alarm',
    },
    {
      label: appliedFilters.value.scope === 'all' ? '全部项目预估总额' : '在招项目预估总额',
      value: totalAmount.toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
      unit: '亿元',
      note: `A级项目占 ${aPercent}%`,
      tone: 'positive',
      icon: 'account_balance',
    },
  ];
});

const stageLabels = ['线索阶段', '初步对接', '资审报名', '标书编制', '已递交'];
const stages = computed(() => {
  const counts = stageLabels.map(
    (label) => opportunityProjects.value.filter((project) => project.status === label).length,
  );
  const max = Math.max(1, ...counts);
  return stageLabels.map((label, index) => ({
    label,
    count: counts[index] ?? 0,
    value: Math.round(((counts[index] ?? 0) / max) * 100),
  }));
});
const provinceRanking = computed(() => {
  const ranked = provinces
    .filter((item) => item.amount > 0)
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 7);
  const max = ranked[0]?.amount ?? 1;
  return ranked.map((item) => ({ ...item, percent: Math.round((item.amount / max) * 100) }));
});
const ratingData = computed(() =>
  (['A', 'B', 'C', 'D'] as const).map((grade) => {
    const count = filteredProjects.value.filter((project) => project.rating === grade).length;
    return {
      grade,
      percent: filteredProjects.value.length
        ? Math.round((count / filteredProjects.value.length) * 100)
        : 0,
    };
  }),
);
const ratingDonutStyle = computed(() => {
  const [a, b, c] = ratingData.value.map((item) => item.percent);
  const stopA = a ?? 0;
  const stopB = stopA + (b ?? 0);
  const stopC = stopB + (c ?? 0);
  return {
    background: `conic-gradient(#28c6f2 0 ${stopA}%, #357ff0 ${stopA}% ${stopB}%, #f6b947 ${stopB}% ${stopC}%, #f15b78 ${stopC}% 100%)`,
  };
});

const monthlyTrend = computed(() => {
  const now = new Date();
  return Array.from({ length: 12 }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth() - 5 + index, 1);
    const year = date.getFullYear();
    const month = date.getMonth();
    const projects = filteredProjects.value.filter((project) => {
      const value = project.openDate || project.deadline;
      if (!value) return false;
      const target = new Date(value.replace(' ', 'T'));
      return (
        !Number.isNaN(target.getTime()) &&
        target.getFullYear() === year &&
        target.getMonth() === month
      );
    });
    return {
      key: `${year}-${String(month + 1).padStart(2, '0')}`,
      label: `${month + 1}月`,
      total: projects.length,
      priority: projects.filter((project) => project.rating === 'A' || project.rating === 'B')
        .length,
    };
  });
});
const trendMax = computed(() => {
  const maximum = Math.max(1, ...monthlyTrend.value.map((item) => item.total));
  return Math.max(5, Math.ceil(maximum / 5) * 5);
});
const trendAxisLabels = computed(() =>
  Array.from({ length: 5 }, (_, index) => Math.round(trendMax.value * (1 - index / 4))),
);
function trendPoints(field: 'total' | 'priority'): string {
  return monthlyTrend.value
    .map((item, index) => {
      const x = (760 / 11) * index;
      const y = 160 - (item[field] / trendMax.value) * 145;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}
const trendProjectPoints = computed(() => trendPoints('total'));
const trendPriorityPoints = computed(() => trendPoints('priority'));
const trendAreaPath = computed(
  () => `M${trendProjectPoints.value.replaceAll(' ', ' L')} L760 170 L0 170 Z`,
);
const urgentProjects = computed(() =>
  filteredProjects.value.filter((project) => project.days >= 0 && project.days <= 9),
);
const urgentPageSize = 6;
const urgentPage = ref(1);
const urgentPageCount = computed(() =>
  Math.max(1, Math.ceil(urgentProjects.value.length / urgentPageSize)),
);
const pagedUrgentProjects = computed(() => {
  const start = (urgentPage.value - 1) * urgentPageSize;
  return urgentProjects.value.slice(start, start + urgentPageSize);
});
watch(urgentPageCount, (pageCount) => {
  if (urgentPage.value > pageCount) urgentPage.value = pageCount;
});
const topOpportunities = computed(() =>
  [...filteredProjects.value].sort((a, b) => a.days - b.days).slice(0, 3),
);

const amapProjects = computed<AmapProjectPoint[]>(() => {
  return filteredProjects.value.map(
    ({
      dbId,
      id,
      name,
      lng,
      lat,
      amount,
      rating,
      province,
      city,
      district = '',
      owner,
      status,
      locationPrecision,
    }) => ({
      dbId,
      id,
      name,
      lng,
      lat,
      amount,
      rating,
      province,
      city,
      district,
      owner,
      status,
      locationPrecision,
    }),
  );
});

const mapTitle = computed(() => {
  if (mapProvider.value === 'amap') return '高德 GIS 项目分布';
  return mapLevel.value === 'country'
    ? '全国项目热力分布'
    : `${selectedProvince.value?.name ?? ''}地级市项目分布`;
});
const selectedArea = computed(() => selectedCity.value || selectedProvince.value?.name || '');
function normalizeAreaName(value: string): string {
  return value.trim().replace(/(特别行政区|自治州|地区|盟|市)$/u, '');
}
const selectedCityProjects = computed(() => {
  const city = normalizeAreaName(selectedCity.value);
  if (!city) return [];
  return filteredProjects.value.filter(
    (project) =>
      (!selectedProvince.value || project.province === selectedProvince.value.name) &&
      normalizeAreaName(project.city) === city,
  );
});
const areaStats = computed(() => {
  const projects = selectedCity.value
    ? selectedCityProjects.value
    : selectedProvince.value
      ? filteredProjects.value.filter(
          (project) => project.province === selectedProvince.value?.name,
        )
      : filteredProjects.value;
  return {
    total: projects.length,
    tracked: projects.filter((project) => Boolean(project.status) && project.status !== '线索阶段')
      .length,
    pending: projects.filter((project) => project.days >= 0 && project.days <= 30).length,
    amount: Number(projects.reduce((sum, project) => sum + project.amount, 0).toFixed(1)),
  };
});

function isProject(value: unknown): value is Project {
  if (!value || typeof value !== 'object') return false;
  const item = value as Partial<Project>;
  return (
    typeof item.id === 'number' &&
    typeof item.name === 'string' &&
    typeof item.category === 'string' &&
    typeof item.province === 'string' &&
    typeof item.city === 'string' &&
    typeof item.lng === 'number' &&
    Number.isFinite(item.lng) &&
    typeof item.lat === 'number' &&
    Number.isFinite(item.lat) &&
    typeof item.owner === 'string' &&
    typeof item.days === 'number' &&
    typeof item.amount === 'number' &&
    ['', 'A', 'B', 'C', 'D'].includes(item.rating ?? '') &&
    typeof item.status === 'string' &&
    typeof item.ownerPerson === 'string' &&
    typeof item.openDate === 'string' &&
    typeof item.deadline === 'string' &&
    typeof item.competitors === 'string' &&
    typeof item.log === 'string'
  );
}

function amountLabel(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? `${yuanNumberLabel(value)}元` : '—';
}

function toYuanAmount(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value)
    ? Math.round(value * 100_000_000 * 100) / 100
    : null;
}

function yuanNumberLabel(value: number | null | undefined): string {
  const amount = toYuanAmount(value);
  return amount === null
    ? '—'
    : new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }).format(amount);
}

function blankLabel(value: string | null | undefined): string {
  return value?.trim() || '—';
}

function formatTrackingTime(value: string): string {
  if (!value) return '—';
  const date = new Date(value.replace(' ', 'T'));
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false });
}

async function openTrackingEditor(project: Project): Promise<void> {
  if (!project.dbId) {
    trackingError.value = '当前项目尚未关联数据库记录，无法保存跟进信息。';
    return;
  }
  trackingProject.value = project;
  selectedProject.value = null;
  Object.assign(trackingForm, {
    stage: project.status || '线索阶段',
    responsiblePerson: project.ownerPerson || '',
    competitors: project.competitors || '',
    log: '',
    nextFollowUpAt: project.nextFollowUpAt
      ? project.nextFollowUpAt.slice(0, 16).replace(' ', 'T')
      : '',
  });
  trackingHistory.value = [];
  trackingError.value = '';
  trackingSuccess.value = '';
  trackingLoading.value = true;
  try {
    const response = await fetch(`/api/projects/${project.dbId}/tracking`, {
      headers: { Accept: 'application/json' },
    });
    const payload = (await response.json()) as {
      message?: string;
      history?: TrackingHistoryItem[];
    };
    if (!response.ok) throw new Error(payload.message || `跟进记录接口返回 ${response.status}`);
    trackingHistory.value = Array.isArray(payload.history) ? payload.history : [];
  } catch (error) {
    trackingError.value = error instanceof Error ? error.message : '无法读取跟进记录';
  } finally {
    trackingLoading.value = false;
  }
}

function closeTrackingEditor(): void {
  if (trackingSaving.value) return;
  trackingProject.value = null;
  trackingError.value = '';
  trackingSuccess.value = '';
}

async function saveTrackingRecord(): Promise<void> {
  const project = trackingProject.value;
  if (!project?.dbId) return;
  if (!trackingForm.log.trim()) {
    trackingError.value = '请填写本次跟进记录。';
    return;
  }
  trackingSaving.value = true;
  trackingError.value = '';
  trackingSuccess.value = '';
  try {
    const response = await fetch(`/api/projects/${project.dbId}/tracking`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(trackingForm),
    });
    const payload = (await response.json()) as {
      message?: string;
      project?: Project;
      history?: TrackingHistoryItem[];
    };
    if (!response.ok || !payload.project)
      throw new Error(payload.message || `保存接口返回 ${response.status}`);
    const updatedProject = applyRatingRule([payload.project])[0];
    if (!updatedProject) throw new Error('保存成功，但返回的项目数据不完整');
    const index = allProjects.value.findIndex((item) => item.dbId === project.dbId);
    if (index >= 0) allProjects.value.splice(index, 1, updatedProject);
    trackingProject.value = updatedProject;
    trackingHistory.value = Array.isArray(payload.history) ? payload.history : [];
    trackingForm.log = '';
    trackingSuccess.value = '跟进记录已保存，地图与项目台账已同步更新。';
  } catch (error) {
    trackingError.value = error instanceof Error ? error.message : '保存跟进记录失败';
  } finally {
    trackingSaving.value = false;
  }
}

function calculateRating(project: Project, rule = ratingRule.value): ProjectRating {
  const amount = project.amount;
  let score = amount >= 1 ? 40 : amount >= 0.3 ? 32 : amount >= 0.1 ? 24 : amount > 0 ? 14 : 0;
  score +=
    project.days >= 3 && project.days <= 14
      ? 30
      : project.days >= 15 && project.days <= 30
        ? 22
        : project.days >= 0 && project.days < 3
          ? 12
          : project.days > 30
            ? 10
            : 0;
  if (project.owner) score += 10;
  if (project.category) score += 10;
  if (project.city) score += 10;
  if (score >= rule.aMin) return 'A';
  if (score >= rule.bMin) return 'B';
  if (score >= rule.cMin) return 'C';
  return 'D';
}

function applyRatingRule(projects: Project[]): Project[] {
  return projects.map((project) =>
    project.aiRatedAt ? project : { ...project, rating: calculateRating(project) },
  );
}

async function openAiRatingAssistant(): Promise<void> {
  aiRatingError.value = '';
  aiRatingSuccess.value = '';
  showAiRating.value = true;
  try {
    const response = await fetch('/api/cost/ai-status', {
      headers: { Accept: 'application/json' },
    });
    const payload = (await response.json()) as {
      enabled?: boolean;
      model?: string;
      message?: string;
    };
    if (!response.ok) throw new Error(payload.message || `模型状态接口返回 ${response.status}`);
    aiRatingModel.value = payload.model || '';
    if (!payload.enabled)
      aiRatingError.value = 'AI大模型尚未配置或未启用，请先在AI成本测算模块完成模型配置。';
  } catch (error) {
    aiRatingError.value = error instanceof Error ? error.message : '无法读取AI模型配置';
  }
}

function closeAiRatingAssistant(): void {
  if (aiRatingLoading.value || aiRatingApplying.value) return;
  showAiRating.value = false;
}

async function generateAiRatingPreview(): Promise<void> {
  const scopeProjects = aiRatingScope.value === 'all' ? allProjects.value : filteredProjects.value;
  const projectIds = scopeProjects
    .map((project) => project.dbId)
    .filter((id): id is number => typeof id === 'number');
  if (!projectIds.length) {
    aiRatingError.value = '当前范围没有可提交给AI的数据库项目。';
    return;
  }
  aiRatingLoading.value = true;
  aiRatingError.value = '';
  aiRatingSuccess.value = '';
  aiRatingPreview.value = [];
  try {
    const response = await fetch('/api/projects/ai-rating/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ criteria: aiRatingCriteria.value, projectIds }),
    });
    const payload = (await response.json()) as {
      message?: string;
      model?: string;
      ratings?: AiRatingPreviewItem[];
    };
    if (!response.ok) throw new Error(payload.message || `AI评级接口返回 ${response.status}`);
    aiRatingPreview.value = Array.isArray(payload.ratings) ? payload.ratings : [];
    aiRatingModel.value = payload.model || '';
    if (!aiRatingPreview.value.length) throw new Error('AI没有返回有效评级结果');
  } catch (error) {
    aiRatingError.value = error instanceof Error ? error.message : 'AI评级失败';
  } finally {
    aiRatingLoading.value = false;
  }
}

async function applyAiRatings(): Promise<void> {
  if (!aiRatingPreview.value.length) return;
  aiRatingApplying.value = true;
  aiRatingError.value = '';
  aiRatingSuccess.value = '';
  try {
    const response = await fetch('/api/projects/ai-rating/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ criteria: aiRatingCriteria.value, ratings: aiRatingPreview.value }),
    });
    const payload = (await response.json()) as { message?: string; affectedRows?: number };
    if (!response.ok) throw new Error(payload.message || `评级写入接口返回 ${response.status}`);
    const previewMap = new Map(aiRatingPreview.value.map((item) => [item.id, item]));
    const ratedAt = new Date().toISOString();
    allProjects.value = allProjects.value.map((project) => {
      const item = typeof project.dbId === 'number' ? previewMap.get(project.dbId) : undefined;
      return item
        ? {
            ...project,
            rating: item.rating,
            aiRatingReason: item.reason,
            aiRatingCriteria: aiRatingCriteria.value,
            aiRatedAt: ratedAt,
          }
        : project;
    });
    aiRatingSuccess.value =
      payload.message ||
      `已更新 ${payload.affectedRows ?? aiRatingPreview.value.length} 个项目的AI评级`;
    aiRatingPreview.value = [];
  } catch (error) {
    aiRatingError.value = error instanceof Error ? error.message : '应用AI评级失败';
  } finally {
    aiRatingApplying.value = false;
  }
}

function openRatingSettings(): void {
  Object.assign(ratingDraft, ratingRule.value);
  ratingRuleError.value = '';
  showRatingSettings.value = true;
}

function closeRatingSettings(): void {
  showRatingSettings.value = false;
  ratingRuleError.value = '';
}

function restoreDefaultRatingRule(): void {
  Object.assign(ratingDraft, defaultRatingRule);
  ratingRuleError.value = '';
}

function saveRatingSettings(): void {
  if (ratingDraft.mode === 'system') Object.assign(ratingDraft, defaultRatingRule);
  if (!(
    ratingDraft.aMin > ratingDraft.bMin &&
    ratingDraft.bMin > ratingDraft.cMin &&
    ratingDraft.cMin > 0 &&
    ratingDraft.aMin <= 100
  )) {
    ratingRuleError.value = '分值必须满足：100 ≥ A级 > B级 > C级 > 0。';
    return;
  }
  ratingRule.value = { ...ratingDraft };
  localStorage.setItem('bidding-rating-rule', JSON.stringify(ratingRule.value));
  allProjects.value = applyRatingRule(allProjects.value);
  closeRatingSettings();
}

async function openUpdateHistory(): Promise<void> {
  showUpdateHistory.value = true;
  historyLoading.value = true;
  historyError.value = '';
  historyPage.value = 1;
  try {
    const historyResponse = await fetch(`/data/update-history.json?t=${Date.now()}`, {
      cache: 'no-store',
    });
    if (!historyResponse.ok) throw new Error(`更新记录返回 ${historyResponse.status}`);
    const payload = (await historyResponse.json()) as unknown;
    if (!Array.isArray(payload)) throw new Error('更新记录格式不正确');
    const retentionStart = Date.now() - 7 * 24 * 60 * 60 * 1000;
    updateHistory.value = payload
      .filter(
        (item): item is UpdateHistoryRecord =>
          Boolean(item) &&
          typeof item === 'object' &&
          typeof (item as UpdateHistoryRecord).success === 'boolean' &&
          typeof (item as UpdateHistoryRecord).updatedAt === 'string' &&
          new Date((item as UpdateHistoryRecord).updatedAt.replace(' ', 'T')).getTime() >=
            retentionStart,
      )
      .sort(
        (a, b) =>
          new Date(b.updatedAt.replace(' ', 'T')).getTime() -
          new Date(a.updatedAt.replace(' ', 'T')).getTime(),
      );
  } catch (error) {
    historyError.value = error instanceof Error ? error.message : '无法读取更新记录';
  } finally {
    historyLoading.value = false;
  }
}

function gradeClass(rating: ProjectRating): string {
  return rating ? `grade-${rating.toLowerCase()}` : 'grade-unrated';
}

function locationLabel(project: Project): string {
  return [project.province, project.city, project.district].filter(Boolean).join(' · ') || '—';
}

async function loadProjectData(): Promise<void> {
  if (!projectApiUrl) {
    allProjects.value = applyRatingRule(demoProjects);
    dataSourceMode.value = 'demo';
    return;
  }

  try {
    const response = await fetch(projectApiUrl, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`项目接口返回 ${response.status}`);
    const payload = (await response.json()) as unknown;
    const fetchedAt = Array.isArray(payload)
      ? ''
      : ((payload as { fetchedAt?: unknown } | null)?.fetchedAt ?? '');
    const rawProjects = Array.isArray(payload)
      ? payload
      : (payload as { data?: unknown } | null)?.data;
    if (!Array.isArray(rawProjects)) throw new Error('项目接口数据格式不正确');
    const projects = rawProjects.filter(isProject);
    if (!projects.length && rawProjects.length) throw new Error('项目数据缺少必要字段');
    allProjects.value = applyRatingRule(projects);
    if (typeof fetchedAt === 'string' && fetchedAt) {
      const date = new Date(fetchedAt);
      dataUpdatedAt.value = Number.isNaN(date.getTime())
        ? fetchedAt
        : date.toLocaleString('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          });
    }
    dataSourceMode.value = 'live';
  } catch (error) {
    console.error('加载真实项目数据失败：', error);
    allProjects.value = applyRatingRule(demoProjects);
    dataSourceMode.value = 'error';
  }
}

function buildProvinceDatum(name: string, adcode: string): ProvinceDatum {
  const projects = filteredProjects.value.filter((project) => project.province === name);
  const ratingScore: Record<Exclude<ProjectRating, ''>, number> = { A: 100, B: 75, C: 50, D: 20 };
  const ratedProjects = projects.filter(
    (project): project is Project & { rating: Exclude<ProjectRating, ''> } =>
      Boolean(project.rating),
  );
  const rating = ratedProjects.length
    ? Math.round(
        ratedProjects.reduce((sum, project) => sum + ratingScore[project.rating], 0) /
          ratedProjects.length,
      )
    : 0;
  return {
    name,
    adcode,
    count: projects.length,
    tracked: projects.filter(isOpportunityProject).length,
    pending: projects.filter((project) => project.days >= 0 && project.days <= 30).length,
    amount: Number(projects.reduce((sum, project) => sum + project.amount, 0).toFixed(1)),
    rating,
  };
}

function metricValue(item: ProvinceDatum): number {
  if (mapMode.value === 'tracking') return item.tracked;
  if (mapMode.value === 'rating') return item.rating;
  return item.count;
}

function renderMap(
  mapName = activeMapName.value,
  cityData?: { name: string; value: number }[],
): void {
  if (!mapChart) return;
  const data = cityData ?? provinces.map((item) => ({ name: item.name, value: metricValue(item) }));
  const maximum = Math.max(1, ...data.map((item) => Number(item.value) || 0));
  const modeColors: Record<MapMode, string[]> = {
    count: ['#082f63', '#0d78c7', '#55dcff'],
    tracking: ['#082f45', '#087e78', '#32e2b0'],
    rating: ['#30235f', '#7652c9', '#ffbd55'],
  };
  mapChart.setOption(
    {
      animationDuration: 700,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(3, 22, 54, .96)',
        borderColor: 'rgba(66, 190, 255, .55)',
        borderWidth: 1,
        textStyle: { color: '#dff5ff', fontSize: 14, lineHeight: 22 },
        extraCssText: 'box-shadow:0 12px 30px rgba(0,0,0,.35);border-radius:5px;',
        formatter: (params: { name: string; value?: number }) => {
          if (mapLevel.value === 'province') {
            const cityProjects = filteredProjects.value.filter(
              (project) =>
                project.province === selectedProvince.value?.name &&
                normalizeAreaName(project.city) === normalizeAreaName(params.name),
            );
            const cityAmount = cityProjects.reduce((sum, project) => sum + project.amount, 0);
            return `<div style="min-width:190px"><b style="font-size:16px;color:#fff">${params.name}</b><div style="margin:9px 0;border-top:1px solid rgba(100,180,255,.2)"></div>项目总数：<b>${cityProjects.length}</b> 项<br/>待开标项目：<b style="color:#ff7591">${cityProjects.filter(isOpportunityProject).length}</b> 项<br/>总造价金额：<b>${yuanNumberLabel(cityAmount)}</b> 元</div>`;
          }
          const province = provinces.find((item) => item.name === params.name);
          if (!province)
            return `<strong>${params.name}</strong><br/>项目数量：${params.value ?? 0}`;
          return `<div style="min-width:210px"><b style="font-size:16px;color:#fff">${params.name}</b><div style="margin:9px 0;border-top:1px solid rgba(100,180,255,.2)"></div>项目总数：<b>${province.count}</b> 项<br/>在跟踪项目：<b>${province.tracked}</b> 项<br/>待开标项目：<b style="color:#ff7591">${province.pending}</b> 项<br/>总造价金额：<b>${yuanNumberLabel(province.amount)}</b> 元</div>`;
        },
      },
      visualMap: {
        show: false,
        min: 0,
        max: mapMode.value === 'rating' ? 100 : maximum,
        inRange: { color: modeColors[mapMode.value] },
      },
      series: [
        {
          type: 'map',
          map: mapName,
          roam: true,
          layoutCenter: ['50%', mapLevel.value === 'country' ? '55%' : '52%'],
          layoutSize: mapLevel.value === 'country' ? '92%' : '88%',
          zoom: mapLevel.value === 'country' ? 1.12 : 1,
          data,
          label: {
            show: mapLevel.value === 'province',
            color: '#d9effb',
            fontSize: 11,
            formatter: (params: { name: string; value?: number }) => {
              const suffix = mapMode.value === 'rating' ? '分' : '项';
              return `${params.name}\n${Number(params.value) || 0}${suffix}`;
            },
          },
          itemStyle: {
            areaColor: '#0a4383',
            borderColor: '#2f9ddd',
            borderWidth: 0.8,
            shadowColor: 'rgba(20,146,255,.2)',
            shadowBlur: 8,
          },
          emphasis: {
            label: { show: true, color: '#fff', fontWeight: 600 },
            itemStyle: {
              areaColor: '#16a8e4',
              borderColor: '#72efff',
              borderWidth: 1.4,
              shadowColor: '#19baff',
              shadowBlur: 18,
            },
          },
          select: {
            label: { color: '#fff' },
            itemStyle: { areaColor: '#147fe0', borderColor: '#72efff' },
          },
        },
      ],
    },
    true,
  );
}

async function drillProvince(province: ProvinceDatum): Promise<void> {
  try {
    const response = await fetch(`/data/maps/${province.adcode}.json`);
    if (!response.ok) throw new Error('map data unavailable');
    const geoJson = (await response.json()) as GeoJson;
    const mapName = `province-${province.adcode}`;
    echarts.registerMap(mapName, geoJson as Parameters<typeof echarts.registerMap>[1]);
    const provinceProjects = filteredProjects.value.filter(
      (project) => project.province === province.name,
    );
    const cities = (geoJson.features ?? []).map((feature, index) => {
      const name = feature.properties?.name ?? `区域${index + 1}`;
      const cityProjects = provinceProjects.filter(
        (project) => normalizeAreaName(project.city) === normalizeAreaName(name),
      );
      const value =
        mapMode.value === 'rating'
          ? cityProjects.length
            ? Math.round(
                cityProjects.reduce(
                  (sum, project) => sum + { A: 100, B: 75, C: 50, D: 20, '': 0 }[project.rating],
                  0,
                ) / cityProjects.length,
              )
            : 0
          : mapMode.value === 'tracking'
            ? cityProjects.filter(
                (project) => Boolean(project.status) && project.status !== '线索阶段',
              ).length
            : cityProjects.length;
      return { name, value };
    });
    selectedProvince.value = province;
    selectedCity.value = '';
    mapLevel.value = 'province';
    activeMapName.value = mapName;
    renderMap(mapName, cities);
  } catch {
    selectedProvince.value = province;
  }
}

function resetMap(): void {
  mapLevel.value = 'country';
  activeMapName.value = 'china';
  selectedProvince.value = null;
  selectedCity.value = '';
  renderMap('china');
}
function clearArea(): void {
  if (mapLevel.value === 'province') resetMap();
  else {
    selectedProvince.value = null;
    selectedCity.value = '';
  }
}
function closeCityProjects(): void {
  selectedCity.value = '';
}
function openProjectFromCity(project: Project): void {
  selectedCity.value = '';
  selectedProject.value = project;
}
function daysUntil(date: string): number {
  const normalizedDate = date.includes(' ') ? date.replace(' ', 'T') : `${date}T23:59:59`;
  const target = new Date(normalizedDate);
  if (Number.isNaN(target.getTime())) return Number.POSITIVE_INFINITY;
  return Math.ceil((target.getTime() - Date.now()) / 86_400_000);
}
function countdownLabel(project: Project): string {
  if (!isOpportunityProject(project)) return '已截止';
  return project.openDate ? `${project.days}天（距开标）` : `${project.days}天（距截止）`;
}
function applyFilters(): void {
  appliedFilters.value = { ...filters.value };
}
function applyScopeFilter(scope: string | null): void {
  if (scope !== 'opportunity' && scope !== 'all') return;
  // 项目范围是页面主视图开关，选择后立即刷新统计、地图和项目台账。
  // 其他筛选条件仍由“检索”按钮统一提交。
  appliedFilters.value = { ...appliedFilters.value, scope };
  ledgerPage.value = 1;
}
function resetFilters(): void {
  const defaults = createDefaultFilters();
  filters.value = { ...defaults };
  appliedFilters.value = { ...defaults };
}
function scrollToLedger(): void {
  ledgerElement.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleAmapProjectClick(point: AmapProjectPoint): void {
  selectedProject.value = allProjects.value.find((project) => project.id === point.id) ?? null;
}

function exportLedger(): void {
  const headers = [
    '评级',
    '项目名称',
    '工程类型',
    '省份',
    '城市',
    '业主单位',
    '公告发布日期',
    '开标日期',
    '投标截止日',
    '招标控制价(元)',
    '预估合同额(元)',
    '暂列金额(元)',
    '跟踪阶段',
    '责任人',
  ];
  const rows = filteredProjects.value.map((item) => [
    item.rating,
    item.name,
    item.category,
    item.province,
    item.city,
    item.owner,
    item.announcementDate ?? '',
    item.openDate,
    item.deadline,
    toYuanAmount(item.controlPrice) ?? '',
    toYuanAmount(item.estimatedContractAmount) ?? '',
    toYuanAmount(item.provisionalSum) ?? '',
    item.status,
    item.ownerPerson,
  ]);
  const table = [headers, ...rows]
    .map(
      (row) =>
        `<Row>${row.map((cell) => `<Cell><Data ss:Type="String">${String(cell).replace(/[<>&]/g, '')}</Data></Cell>`).join('')}</Row>`,
    )
    .join('');
  const content = `<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="项目台账"><Table>${table}</Table></Worksheet></Workbook>`;
  const link = document.createElement('a');
  link.href = URL.createObjectURL(
    new Blob([content], { type: 'application/vnd.ms-excel;charset=utf-8' }),
  );
  link.download = `全国项目台账-${new Date().toISOString().slice(0, 10)}.xls`;
  link.click();
  URL.revokeObjectURL(link.href);
}

watch(mapMode, () => {
  if (mapLevel.value === 'country') renderMap('china');
  else if (selectedProvince.value) void drillProvince(selectedProvince.value);
});

watch(filteredProjects, () => {
  ledgerPage.value = 1;
  provinces.forEach((province) => {
    Object.assign(province, buildProvinceDatum(province.name, province.adcode));
  });
  if (mapLevel.value === 'country') renderMap('china');
  else if (selectedProvince.value) void drillProvince(selectedProvince.value);
});

watch(mapProvider, async (provider) => {
  if (provider !== 'echarts') return;
  await nextTick();
  mapChart?.resize();
});

onMounted(async () => {
  await nextTick();
  await loadProjectData();
  const response = await fetch('/data/china.json');
  const geoJson = (await response.json()) as GeoJson;
  (geoJson.features ?? []).forEach((feature) => {
    const name = feature.properties?.name;
    const adcode = String(feature.properties?.adcode ?? '');
    if (!name || !/^\d{6}$/.test(adcode) || provinces.some((item) => item.name === name)) return;
    provinces.push(buildProvinceDatum(name, adcode));
  });
  echarts.registerMap('china', geoJson as Parameters<typeof echarts.registerMap>[1]);
  if (!mapElement.value) return;
  mapChart = echarts.init(mapElement.value);
  renderMap();
  mapChart.on('click', (params) => {
    const areaName = String(params.name ?? '');
    if (mapLevel.value === 'country') {
      const province = provinces.find((item) => item.name === areaName);
      if (province) void drillProvince(province);
    } else {
      selectedCity.value = areaName;
    }
  });
  resizeObserver = new ResizeObserver(() => mapChart?.resize());
  resizeObserver.observe(mapElement.value);
  projectRefreshTimer = setInterval(() => void loadProjectData(), 5 * 60_000);
});

onBeforeUnmount(() => {
  if (projectRefreshTimer) clearInterval(projectRefreshTimer);
  resizeObserver?.disconnect();
  mapChart?.dispose();
});
</script>

<style scoped lang="scss">
.dashboard-page {
  min-width: 0;
}
.dashboard-heading {
  margin-bottom: 18px;
}
.heading-actions {
  display: flex;
  align-items: center;
  gap: 9px;
}
.status-pill--demo {
  color: #ffc86a;
  border-color: rgb(255 189 79 / 28%);
}
.primary-button,
.history-button,
.ai-rating-button,
.search-button,
.filter-button,
.area-action,
.dialog-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #f2fbff;
  background: linear-gradient(180deg, #128eea, #0b5db8);
  border: 1px solid rgb(75 194 255 / 48%);
  border-radius: 4px;
  box-shadow:
    inset 0 1px rgb(255 255 255 / 11%),
    0 0 18px rgb(18 126 232 / 14%);
  font: inherit;
  cursor: pointer;
}
.primary-button,
.history-button,
.ai-rating-button {
  min-height: 34px;
  padding: 0 14px;
  font-size: 12px;
}
.history-button {
  color: #a9daf4;
  background: rgb(7 48 98 / 78%);
  border-color: rgb(66 170 232 / 28%);
  box-shadow: none;
}
.ai-rating-button {
  color: #dff9ff;
  background: linear-gradient(180deg, rgb(23 137 177 / 82%), rgb(19 82 154 / 88%));
  border-color: rgb(74 222 255 / 38%);
}
.filter-bar {
  display: flex;
  align-items: end;
  gap: 10px;
  margin-bottom: 14px;
  padding: 13px 14px;
  overflow: visible;
}
.search-field {
  display: flex;
  min-width: 260px;
  min-height: 37px;
  flex: 1;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  color: #5595c6;
  background: rgb(2 23 57 / 52%);
  border: 1px solid rgb(65 150 222 / 23%);
  border-radius: 4px;
}
.search-field input {
  width: 100%;
  color: #d9edff;
  background: transparent;
  border: 0;
  outline: 0;
  font: inherit;
  font-size: 11px;
}
.search-field input::placeholder {
  color: #4c7196;
}
.search-result-count {
  flex: 0 0 auto;
  padding: 3px 8px;
  color: #62cfff;
  background: rgb(18 123 196 / 12%);
  border: 1px solid rgb(71 184 244 / 24%);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
}
.filter-field {
  display: grid;
  min-width: 125px;
  gap: 5px;
}
.filter-field > span {
  color: #648caf;
  font-size: 9px;
}
.dashboard-select {
  min-height: 37px;
  color: #bad4e9;
  border-radius: 4px;
  font: inherit;
  font-size: 11px;
  color-scheme: dark;
}
.dashboard-select :deep(.q-field__control) {
  min-height: 42px;
  height: 42px;
  color: #bad4e9;
  background: #061f45;
  border-radius: 4px;
}
.dashboard-select :deep(.q-field__control::before) {
  border-color: rgb(65 150 222 / 23%);
}
.dashboard-select :deep(.q-field__native),
.dashboard-select :deep(.q-field__input),
.dashboard-select :deep(.q-field__marginal) {
  min-height: 42px;
  height: 42px;
  color: #bad4e9;
  font-size: 11px;
}
.dashboard-select :deep(.q-field__native) {
  padding: 0 0 0 10px;
}
:global(.dashboard-select-popup) {
  color: #c9def0;
  background: #0a3768;
  border: 1px solid rgb(66 174 239 / 38%);
  border-radius: 3px;
  box-shadow: 0 12px 30px rgb(0 8 28 / 48%);
}
:global(.dashboard-select-popup .q-item) {
  min-height: 38px;
  color: #c9def0;
  font-size: 13px;
}
:global(.dashboard-select-popup .q-item:hover:not(.q-item--active)) {
  background: #0d477e;
}
:global(.dashboard-select-popup .q-item--active),
:global(.dashboard-select-popup .q-item[aria-selected='true']) {
  color: #fff !important;
  background: #02142f !important;
  font-weight: 600;
}
:global(.dashboard-select-popup .q-item[aria-selected='false'].q-manual-focusable--focused) {
  background: #0d477e !important;
}
:global(.dashboard-select-popup .q-item .q-focus-helper) {
  display: none !important;
}
.search-button,
.filter-button {
  min-height: 37px;
  padding: 0 13px;
  white-space: nowrap;
  font-size: 11px;
}
.search-button {
  min-width: 76px;
}
.filter-button {
  color: #8db6d7;
  background: rgb(14 77 139 / 35%);
  box-shadow: none;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 14px;
}
.metric-card {
  display: grid;
  min-height: 88px;
  grid-template-columns: 39px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 15px;
}
.metric-icon {
  display: grid;
  width: 39px;
  height: 39px;
  place-items: center;
  color: #67d7ff;
  background: rgb(21 126 222 / 17%);
  border: 1px solid rgb(63 178 245 / 24%);
  border-radius: 5px;
}
.metric-card div > span {
  display: block;
  color: #739abc;
  font-size: 10px;
}
.metric-card strong {
  display: block;
  margin-top: 3px;
  color: #fff;
  font-size: 23px;
  font-weight: 600;
}
.metric-card small {
  margin-left: 3px;
  color: #769aba;
  font-size: 10px;
  font-weight: 400;
}
.metric-card em {
  align-self: end;
  color: #4f789d;
  font-size: 9px;
  font-style: normal;
}
.metric-card em.positive {
  color: #39cda1;
}
.metric-card em.danger {
  color: #ff718b;
}
.metric-card em.info {
  color: #62c9f5;
}
.daily-additions-panel {
  margin-bottom: 14px;
  overflow: hidden;
}
.daily-additions-heading {
  padding: 15px 18px 12px;
}
.daily-additions-heading > div {
  display: grid;
  gap: 4px;
}
.daily-additions-heading p {
  margin: 0;
  color: #638bad;
  font-size: 10px;
}
.daily-additions-body {
  display: grid;
  grid-template-columns: minmax(150px, 185px) minmax(0, 1fr);
  min-height: 250px;
  border-top: 1px solid rgb(65 150 222 / 17%);
}
.daily-date-strip {
  display: grid;
  align-content: start;
  background: rgb(3 25 58 / 38%);
  border-right: 1px solid rgb(65 150 222 / 17%);
}
.daily-date-strip button {
  display: grid;
  min-height: 54px;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  align-items: center;
  padding: 9px 14px;
  color: #7da5c5;
  background: transparent;
  border: 0;
  border-bottom: 1px solid rgb(65 150 222 / 10%);
  text-align: left;
  cursor: pointer;
}
.daily-date-strip button:hover {
  background: rgb(17 103 186 / 10%);
}
.daily-date-strip button.active {
  color: #dff5ff;
  background: linear-gradient(90deg, rgb(12 111 201 / 27%), rgb(8 54 108 / 15%));
  box-shadow: inset 3px 0 #42cfff;
}
.daily-date-strip span {
  font-size: 11px;
}
.daily-date-strip strong {
  grid-row: 1 / 3;
  grid-column: 2;
  color: #5cddff;
  font-size: 20px;
}
.daily-date-strip strong small {
  margin-left: 2px;
  color: #6c96b6;
  font-size: 9px;
  font-weight: 400;
}
.daily-date-strip em {
  font-size: 9px;
  font-style: normal;
}
.daily-projects {
  min-width: 0;
  padding: 11px 14px 14px;
}
.daily-projects-summary {
  display: flex;
  min-height: 34px;
  align-items: center;
  justify-content: space-between;
  color: #7198b9;
  font-size: 10px;
}
.daily-projects-summary b {
  margin-right: 5px;
  color: #b8daef;
}
.daily-projects-summary strong {
  color: #47dcb1;
  font-size: 11px;
}
.daily-project-list {
  display: grid;
  max-height: 330px;
  overflow: auto;
  border: 1px solid rgb(65 150 222 / 15%);
}
.daily-project-item {
  display: grid;
  min-width: 0;
  grid-template-columns: 30px minmax(240px, 1fr) minmax(125px, 0.38fr) minmax(165px, 0.48fr) 18px;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  color: inherit;
  background: rgb(5 37 77 / 42%);
  border: 0;
  border-bottom: 1px solid rgb(65 150 222 / 12%);
  text-align: left;
  cursor: pointer;
}
.daily-project-item:last-child {
  border-bottom: 0;
}
.daily-project-item:hover {
  background: rgb(15 83 150 / 24%);
}
.daily-project-rating {
  display: grid;
  width: 27px;
  height: 27px;
  place-items: center;
  color: #d9f5ff;
  background: rgb(40 137 215 / 22%);
  border: 1px solid rgb(77 183 245 / 30%);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}
.daily-project-rating.grade-a {
  color: #49e0b1;
  border-color: rgb(73 224 177 / 35%);
}
.daily-project-rating.grade-b {
  color: #5ed0ff;
}
.daily-project-rating.grade-c {
  color: #ffc468;
  border-color: rgb(255 196 104 / 35%);
}
.daily-project-rating.grade-d {
  color: #ff8298;
  border-color: rgb(255 130 152 / 35%);
}
.daily-project-name,
.daily-project-amount,
.daily-project-deadline {
  display: grid;
  min-width: 0;
  gap: 4px;
}
.daily-project-name strong {
  overflow: hidden;
  color: #d9efff;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.daily-project-name small,
.daily-project-amount small,
.daily-project-deadline small {
  color: #6389aa;
  font-size: 9px;
}
.daily-project-amount b,
.daily-project-deadline b {
  overflow: hidden;
  color: #9fc6df;
  font-size: 10px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.daily-project-item > .q-icon {
  color: #4386b7;
}
.daily-additions-empty {
  display: grid;
  min-height: 140px;
  place-items: center;
  color: #6086a7;
  border-top: 1px solid rgb(65 150 222 / 17%);
  font-size: 11px;
}
.dashboard-grid {
  display: grid;
  grid-template-columns: 245px minmax(560px, 1fr) 260px;
  gap: 14px;
  margin-bottom: 14px;
}
.alert-panel,
.ranking-panel,
.map-panel {
  min-height: 530px;
}
.map-panel {
  display: flex;
  flex-direction: column;
}
.danger-count {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  color: #ffb2be;
  background: rgb(237 59 90 / 18%);
  border: 1px solid rgb(255 103 126 / 26%);
  border-radius: 50%;
  font-size: 10px;
}
.alert-list {
  padding: 9px;
}
.alert-pagination {
  display: flex;
  min-height: 42px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 5px 8px;
  color: #79a8ca;
  border-top: 1px solid rgb(71 148 219 / 12%);
  font-size: 10px;
}
.alert-item {
  display: grid;
  width: 100%;
  grid-template-columns: 40px 1fr 23px;
  align-items: center;
  gap: 8px;
  padding: 10px 7px;
  color: inherit;
  background: transparent;
  border: 0;
  border-bottom: 1px solid rgb(70 143 211 / 11%);
  text-align: left;
  cursor: pointer;
}
.alert-item:hover {
  background: rgb(22 115 204 / 12%);
}
.alert-days {
  display: grid;
  width: 36px;
  height: 36px;
  place-content: center;
  color: #ffc45f;
  background: rgb(230 149 29 / 12%);
  border: 1px solid rgb(255 184 63 / 22%);
  border-radius: 4px;
  font-size: 15px;
  font-weight: 600;
  text-align: center;
}
.alert-days small {
  font-size: 8px;
  font-weight: 400;
}
.alert-days.critical {
  color: #ff7189;
  background: rgb(233 51 87 / 13%);
  border-color: rgb(255 93 123 / 25%);
}
.alert-content {
  min-width: 0;
}
.alert-content strong {
  display: block;
  overflow: hidden;
  color: #cfe6f8;
  font-size: 10px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.alert-content em {
  display: block;
  margin-top: 5px;
  color: #4f789c;
  font-size: 8px;
  font-style: normal;
}
.alert-item > b {
  display: grid;
  width: 21px;
  height: 21px;
  place-items: center;
  color: #fff;
  background: #e8465e;
  border-radius: 3px;
  font-size: 10px;
}
.stage-summary {
  padding: 7px 16px 16px;
  border-top: 1px solid rgb(71 148 219 / 12%);
}
.mini-heading {
  margin: 9px 0 13px;
  color: #91b2cf;
  font-size: 11px;
  font-weight: 500;
}
.stage-row {
  display: grid;
  grid-template-columns: 56px 1fr 20px;
  align-items: center;
  gap: 7px;
  margin: 9px 0;
  color: #6289aa;
  font-size: 8px;
}
.stage-row > i {
  height: 4px;
  overflow: hidden;
  background: rgb(39 101 158 / 26%);
  border-radius: 4px;
}
.stage-row > i b {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #136fe0, #35d0f4);
  border-radius: 4px;
}
.stage-row em {
  color: #80a6c5;
  font-style: normal;
  text-align: right;
}
.map-heading {
  padding-right: 12px;
}
.map-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.back-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 7px;
  color: #72cfff;
  background: rgb(16 104 190 / 22%);
  border: 1px solid rgb(65 176 243 / 24%);
  border-radius: 3px;
  font: inherit;
  font-size: 9px;
  cursor: pointer;
}
.map-switches,
.map-provider,
.map-modes {
  display: flex;
  gap: 5px;
}
.map-switches {
  align-items: center;
  gap: 8px;
}
.map-provider {
  padding-right: 8px;
  border-right: 1px solid rgb(67 144 211 / 18%);
}
.map-provider button,
.map-modes button {
  padding: 6px 9px;
  color: #6188aa;
  background: rgb(3 27 63 / 40%);
  border: 1px solid rgb(62 137 207 / 17%);
  border-radius: 3px;
  font: inherit;
  font-size: 9px;
  cursor: pointer;
}
.map-provider button.active,
.map-modes button.active {
  color: #c9f1ff;
  background: rgb(16 114 215 / 30%);
  border-color: rgb(60 188 255 / 40%);
}
.map-body {
  position: relative;
  min-height: 474px;
  flex: 1;
  overflow: hidden;
  background:
    radial-gradient(circle at center, rgb(14 102 200 / 15%), transparent 57%),
    linear-gradient(rgb(36 106 179 / 5%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(36 106 179 / 5%) 1px, transparent 1px);
  background-size:
    auto,
    30px 30px,
    30px 30px;
}
.echarts-map {
  width: 100%;
  height: 100%;
}
.map-legend {
  position: absolute;
  bottom: 17px;
  left: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #557d9f;
  font-size: 8px;
}
.map-legend i {
  width: 75px;
  height: 5px;
  background: linear-gradient(90deg, #0a376d, #096db8, #21d0ed);
  border-radius: 3px;
}
.map-hint {
  position: absolute;
  right: 16px;
  bottom: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #477497;
  font-size: 8px;
}
.map-mode-note {
  position: absolute;
  z-index: 2;
  bottom: 14px;
  left: 50%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  color: #7fa7c5;
  background: rgb(3 24 57 / 86%);
  border: 1px solid rgb(65 157 222 / 18%);
  border-radius: 3px;
  font-size: 10px;
  transform: translateX(-50%);
  backdrop-filter: blur(6px);
}
.map-mode-note b {
  color: #bfe8f8;
  font-weight: 600;
}
.map-empty-note {
  position: absolute;
  z-index: 2;
  top: 50%;
  left: 50%;
  padding: 12px 16px;
  color: #a9c6d9;
  background: rgb(3 24 57 / 91%);
  border: 1px solid rgb(69 166 225 / 27%);
  border-radius: 4px;
  font-size: 12px;
  transform: translate(-50%, -50%);
  backdrop-filter: blur(7px);
}
.area-card {
  position: absolute;
  top: 13px;
  right: 13px;
  width: 210px;
  padding: 13px;
  background: rgb(3 25 59 / 91%);
  border: 1px solid rgb(62 181 246 / 29%);
  border-radius: 5px;
  box-shadow: 0 12px 30px rgb(0 7 26 / 32%);
  backdrop-filter: blur(7px);
}
.area-card__head {
  display: flex;
  justify-content: space-between;
}
.area-card__head span {
  display: block;
  color: #4d769a;
  font-size: 8px;
}
.area-card__head strong {
  display: block;
  margin-top: 3px;
  color: #edfaff;
  font-size: 14px;
  font-weight: 600;
}
.area-card__head button {
  color: #5e86a8;
  background: transparent;
  border: 0;
  cursor: pointer;
}
.area-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 12px 0;
}
.area-stats div {
  padding: 8px;
  background: rgb(18 79 143 / 20%);
  border: 1px solid rgb(54 137 208 / 14%);
}
.area-stats span {
  display: block;
  color: #5f88aa;
  font-size: 8px;
}
.area-stats b {
  display: block;
  margin-top: 3px;
  color: #d9f0ff;
  font-size: 13px;
}
.area-stats b.danger {
  color: #ff728d;
}
.area-action {
  width: 100%;
  min-height: 29px;
  font-size: 9px;
}
.ranking-list {
  padding: 12px 14px 8px;
}
.ranking-row {
  display: grid;
  grid-template-columns: 22px 1fr 34px;
  align-items: center;
  gap: 8px;
  margin: 13px 0;
}
.ranking-row > b {
  color: #52799c;
  font-size: 10px;
}
.ranking-row > b.top {
  color: #54d2ff;
}
.ranking-row > div span {
  display: block;
  color: #a4c0d8;
  font-size: 9px;
}
.ranking-row > div i {
  display: block;
  height: 4px;
  margin-top: 5px;
  overflow: hidden;
  background: rgb(34 92 148 / 28%);
  border-radius: 3px;
}
.ranking-row > div em {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #176ce0, #2ed2ee);
  border-radius: 3px;
}
.ranking-row > strong {
  color: #b9d7eb;
  font-size: 9px;
  text-align: right;
}
.rating-block {
  margin: 0 14px;
  padding-top: 3px;
  border-top: 1px solid rgb(70 143 211 / 12%);
}
.rating-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rating-settings-button {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 6px;
  color: #69c9f2;
  background: rgb(18 104 181 / 18%);
  border: 1px solid rgb(66 174 235 / 22%);
  border-radius: 3px;
  font: inherit;
  font-size: 9px;
  cursor: pointer;
}
.rating-chart {
  display: grid;
  grid-template-columns: 108px 1fr;
  align-items: center;
  gap: 11px;
}
.rating-donut {
  display: grid;
  width: 102px;
  height: 102px;
  place-items: center;
  background: conic-gradient(#28c6f2 0 38%, #357ff0 38% 72%, #f6b947 72% 92%, #f15b78 92% 100%);
  border-radius: 50%;
  box-shadow: 0 0 22px rgb(25 144 230 / 16%);
}
.rating-donut::before {
  grid-area: 1/1;
  width: 68px;
  height: 68px;
  content: '';
  background: #082451;
  border-radius: 50%;
}
.rating-donut span {
  z-index: 1;
  grid-area: 1/1;
  text-align: center;
}
.rating-donut strong {
  display: block;
  color: #fff;
  font-size: 19px;
}
.rating-donut small {
  color: #5d83a5;
  font-size: 8px;
}
.rating-legend {
  display: grid;
  gap: 8px;
}
.rating-legend div {
  display: grid;
  grid-template-columns: 7px 1fr auto;
  align-items: center;
  gap: 6px;
  color: #789dbb;
  font-size: 8px;
}
.rating-legend i {
  width: 7px;
  height: 7px;
  border-radius: 2px;
}
.rating-legend b {
  color: #bdd7e9;
  font-weight: 500;
}
.grade-a {
  background: #28c6f2 !important;
}
.grade-b {
  background: #357ff0 !important;
}
.grade-c {
  background: #f6b947 !important;
}
.grade-d {
  background: #f15b78 !important;
}
.lower-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(300px, 0.8fr);
  gap: 14px;
  margin-bottom: 14px;
}
.trend-panel,
.opportunity-panel {
  min-height: 275px;
}
.chart-legend {
  display: flex;
  gap: 14px;
  color: #6388a8;
  font-size: 8px;
}
.chart-legend span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.chart-legend i {
  width: 14px;
  height: 2px;
  background: #30c8ff;
}
.chart-legend span:last-child i {
  background: #507cff;
}
.trend-chart {
  position: relative;
  height: 220px;
  padding: 21px 22px 24px 43px;
  background: repeating-linear-gradient(
    to bottom,
    transparent 0 41px,
    rgb(67 132 194 / 10%) 41px 42px
  );
}
.trend-chart svg {
  width: 100%;
  height: 166px;
  overflow: visible;
}
.axis-labels {
  position: absolute;
  top: 18px;
  bottom: 28px;
  left: 15px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #477194;
  font-size: 8px;
}
.month-labels {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  color: #4d7496;
  font-size: 7px;
  text-align: center;
}
.opportunity-list {
  padding: 8px 13px;
}
.opportunity-list button {
  display: grid;
  width: 100%;
  min-height: 58px;
  grid-template-columns: 27px 1fr auto 15px;
  align-items: center;
  gap: 8px;
  padding: 9px 5px;
  color: inherit;
  background: transparent;
  border: 0;
  border-bottom: 1px solid rgb(72 145 213 / 12%);
  text-align: left;
  cursor: pointer;
}
.opportunity-list button:hover {
  background: rgb(22 112 201 / 10%);
}
.grade-badge {
  display: grid;
  width: 25px;
  height: 25px;
  place-items: center;
  color: #fff;
  background: #20b9df;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}
.opportunity-list strong {
  display: block;
  overflow: hidden;
  color: #c8e1f3;
  font-size: 10px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.opportunity-list em {
  display: block;
  margin-top: 4px;
  color: #4f7598;
  font-size: 8px;
  font-style: normal;
}
.opportunity-list b {
  color: #69d5f6;
  font-size: 10px;
  font-weight: 500;
}
.opportunity-list .q-icon {
  color: #47799f;
}
.ledger-panel {
  scroll-margin-top: 86px;
}
.ledger-scroll {
  overflow-x: auto;
}
.ledger-pagination {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  padding: 10px 16px;
  color: #83a8c6;
  border-top: 1px solid rgb(67 137 202 / 15%);
  font-size: 11px;
}
.ledger-page-size {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ledger-page-size select {
  min-width: 76px;
  height: 32px;
  padding: 0 9px;
  color: #c5e5f7;
  background: #082753;
  border: 1px solid rgb(68 162 229 / 30%);
  border-radius: 4px;
  outline: 0;
  color-scheme: dark;
}
.ledger-pagination :deep(.q-btn) {
  color: #8dc4e5;
}
.ledger-pagination :deep(.q-btn--active) {
  color: #fff;
}
table {
  width: 100%;
  min-width: 1080px;
  border-collapse: collapse;
}
th,
td {
  padding: 12px 13px;
  border-bottom: 1px solid rgb(67 137 202 / 12%);
  text-align: left;
  white-space: nowrap;
}
th {
  color: #668caf;
  background: rgb(6 33 73 / 35%);
  font-size: 9px;
  font-weight: 500;
}
td {
  color: #88a9c5;
  font-size: 9px;
}
td strong {
  color: #c6dfef;
  font-weight: 500;
}
tbody tr {
  cursor: pointer;
  transition: 140ms ease;
}
tbody tr:hover {
  background: rgb(21 107 197 / 13%);
}
.table-grade {
  display: inline-grid;
  width: 23px;
  height: 23px;
  place-items: center;
  color: #fff;
  background: #20b9df;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
}
.deadline-danger {
  color: #ff7089;
  font-weight: 600;
}
.stage-tag {
  padding: 4px 7px;
  color: #72caf1;
  background: rgb(17 111 190 / 18%);
  border: 1px solid rgb(59 161 226 / 18%);
  border-radius: 3px;
}
.project-overlay {
  position: fixed;
  z-index: 7000;
  inset: 0;
  display: grid;
  padding: 30px;
  place-items: center;
  background: rgb(0 8 25 / 72%);
  backdrop-filter: blur(5px);
}
.project-dialog {
  width: min(680px, 100%);
  max-height: calc(100vh - 60px);
  padding: 22px;
  overflow-y: auto;
}
.ai-rating-dialog {
  width: min(1080px, 100%);
  max-height: calc(100vh - 60px);
  padding: 22px;
  overflow-y: auto;
}
.ai-rating-intro {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  padding: 12px 14px;
  margin-top: 15px;
  color: #9dc9e3;
  font-size: 11px;
  line-height: 1.7;
  background: rgb(18 111 179 / 13%);
  border-left: 3px solid #36c9f4;
}
.ai-rating-intro .q-icon {
  margin-top: 2px;
  color: #5ce3ff;
  font-size: 18px;
}
.ai-rating-scope {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  color: #719aba;
  font-size: 10px;
}
.ai-rating-scope button {
  padding: 7px 11px;
  color: #83adca;
  font: inherit;
  background: #071f47;
  border: 1px solid rgb(65 150 218 / 25%);
  border-radius: 3px;
  cursor: pointer;
}
.ai-rating-scope button.active {
  color: #e2f9ff;
  background: rgb(23 126 205 / 28%);
  border-color: #2dbbe9;
}
.ai-rating-criteria {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 14px;
  color: #9fc2da;
  font-size: 10px;
}
.ai-rating-criteria textarea {
  width: 100%;
  padding: 12px 14px;
  color: #dcefff;
  font: inherit;
  line-height: 1.7;
  resize: vertical;
  background: #071f47;
  border: 1px solid rgb(65 150 218 / 35%);
  border-radius: 4px;
  outline: none;
}
.ai-rating-criteria textarea:focus {
  border-color: #27b8f4;
}
.ai-rating-criteria small {
  color: #567e9d;
}
.ai-rating-message {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 0 0;
  font-size: 10px;
}
.ai-rating-message.error {
  color: #ff7d94;
}
.ai-rating-message.success {
  color: #42e4b4;
}
.ai-rating-preview {
  margin-top: 16px;
  border: 1px solid rgb(65 150 218 / 23%);
}
.ai-rating-summary {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 12px;
  color: #789fbd;
  font-size: 10px;
  background: rgb(10 52 103 / 75%);
}
.ai-rating-summary > div {
  display: flex;
  gap: 6px;
}
.ai-rating-summary b {
  padding: 4px 7px;
  font-weight: 600;
  border: 1px solid currentColor;
  border-radius: 3px;
}
.ai-rating-summary strong {
  margin-left: auto;
  color: #55d9ff;
  font-weight: 500;
}
.ai-rating-table-wrap {
  max-height: 330px;
  overflow: auto;
}
.ai-rating-table-wrap table {
  width: 100%;
  border-collapse: collapse;
  color: #a9c8dc;
  font-size: 10px;
}
.ai-rating-table-wrap th,
.ai-rating-table-wrap td {
  padding: 9px 11px;
  text-align: left;
  border-bottom: 1px solid rgb(65 150 218 / 13%);
}
.ai-rating-table-wrap th {
  position: sticky;
  z-index: 1;
  top: 0;
  color: #75a7c9;
  font-weight: 500;
  background: #0a2a59;
}
.ai-rating-table-wrap td:first-child {
  min-width: 240px;
  color: #d1e8f5;
}
.table-grade {
  display: inline-grid;
  width: 25px;
  height: 25px;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 50%;
}
.ai-rating-actions .apply-ai-rating {
  background: linear-gradient(180deg, #15a6c9, #0871b8);
}
.ai-rating-actions button:disabled,
.ai-rating-scope button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
.history-dialog {
  width: min(760px, 100%);
  max-height: calc(100vh - 60px);
  padding: 22px;
  overflow: hidden;
}
.history-dialog__head > div > .q-icon {
  color: #4bc9f4;
}
.history-list {
  display: grid;
  gap: 9px;
  max-height: min(560px, calc(100vh - 170px));
  margin-top: 16px;
  padding-right: 5px;
  overflow-y: auto;
}
.history-item {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  gap: 13px;
  align-items: center;
  padding: 14px;
  background: rgb(6 35 77 / 66%);
  border: 1px solid rgb(69 155 218 / 15%);
  border-radius: 4px;
}
.history-item > i {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  color: #22dc9d;
  background: rgb(24 193 137 / 13%);
  border: 1px solid rgb(35 224 160 / 28%);
  border-radius: 50%;
}
.history-item > i.failed {
  color: #ff7089;
  background: rgb(255 82 113 / 12%);
  border-color: rgb(255 82 113 / 28%);
}
.history-item__main strong,
.history-item__main span,
.history-item__main small {
  display: block;
}
.history-item__main strong {
  color: #dff4ff;
  font-size: 13px;
}
.history-item__main span {
  margin-top: 3px;
  color: #83aaca;
  font-size: 11px;
}
.history-item__main small {
  margin-top: 3px;
  color: #557c9c;
  font-size: 10px;
}
.history-item__main p {
  margin: 5px 0 0;
  color: #ff8fa3;
  font-size: 10px;
}
.history-item__stats {
  display: flex;
  gap: 22px;
}
.history-item__stats span {
  color: #6289a9;
  font-size: 10px;
  text-align: right;
}
.history-item__stats strong {
  display: block;
  margin-top: 3px;
  color: #d8f2ff;
  font-size: 16px;
}
.history-item__stats strong.added {
  color: #27dba0;
}
.history-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 8px 2px 2px;
  color: #7199b9;
  font-size: 11px;
}
.history-pagination button {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 6px 11px;
  color: #bfe7ff;
  background: rgb(18 91 161 / 28%);
  border: 1px solid rgb(73 173 239 / 30%);
  border-radius: 4px;
  cursor: pointer;
}
.history-pagination button:disabled {
  color: #496b86;
  cursor: not-allowed;
  opacity: 0.55;
}
.history-empty {
  padding: 50px 20px;
  color: #7299b9;
  text-align: center;
}
.history-empty--error {
  color: #ff7890;
}
.dialog-head,
.dialog-head > div {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.dialog-head {
  justify-content: space-between;
  padding-bottom: 17px;
  border-bottom: 1px solid rgb(72 155 225 / 17%);
}
.dialog-head small {
  color: #5882a5;
  font-size: 9px;
}
.dialog-head h2 {
  margin: 4px 0 0;
  color: #f2faff;
  font-size: 18px;
  font-weight: 600;
}
.dialog-head > button {
  color: #658bab;
  background: transparent;
  border: 0;
  cursor: pointer;
}
.dialog-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  margin: 16px 0;
  overflow: hidden;
  background: rgb(69 145 211 / 13%);
  border: 1px solid rgb(69 145 211 / 13%);
  border-radius: 4px;
}
.dialog-grid div {
  padding: 12px 14px;
  background: #082653;
}
.dialog-grid span,
.dialog-section > span {
  display: block;
  color: #5f86a8;
  font-size: 8px;
}
.dialog-grid strong {
  display: block;
  margin-top: 5px;
  color: #c8e1f2;
  font-size: 11px;
  font-weight: 500;
}
.dialog-section {
  margin-top: 10px;
  padding: 13px 14px;
  background: rgb(6 31 70 / 52%);
  border: 1px solid rgb(69 145 211 / 12%);
}
.dialog-section p {
  margin: 6px 0 0;
  color: #a6c2d9;
  font-size: 10px;
  line-height: 1.7;
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}
.dialog-actions button {
  min-height: 33px;
  padding: 0 14px;
  font-size: 10px;
}
.dialog-actions .button-link {
  display: inline-flex;
  align-items: center;
  min-height: 33px;
  padding: 0 14px;
  color: #dff7ff;
  font-size: 10px;
  text-decoration: none;
  background: linear-gradient(180deg, #168de0, #0870bd);
  border: 1px solid #25a9ff;
  border-radius: 3px;
}
.tracking-dialog {
  width: min(760px, 100%);
  max-height: calc(100vh - 50px);
  overflow-y: auto;
}
.tracking-project-name {
  margin: 14px 0;
  color: #d9efff;
  font-size: 13px;
  font-weight: 600;
}
.tracking-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.tracking-form-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #83a8c7;
  font-size: 10px;
}
.tracking-form-wide {
  grid-column: 1 / -1;
}
.tracking-form-grid input,
.tracking-form-grid select,
.tracking-form-grid textarea {
  width: 100%;
  padding: 10px 12px;
  color: #d9efff;
  font: inherit;
  background: #071f47;
  border: 1px solid rgb(65 150 218 / 35%);
  border-radius: 4px;
  outline: none;
}
.tracking-form-grid textarea {
  resize: vertical;
}
.tracking-form-grid input:focus,
.tracking-form-grid select:focus,
.tracking-form-grid textarea:focus {
  border-color: #27b8f4;
}
.tracking-message {
  margin: 12px 0 0;
  font-size: 10px;
}
.tracking-message--error {
  color: #ff718d;
}
.tracking-message--success {
  color: #36e6b0;
}
.tracking-history {
  margin-top: 18px;
}
.tracking-history h3 {
  margin: 0 0 9px;
  color: #d5edff;
  font-size: 12px;
}
.tracking-history > article {
  padding: 11px 13px;
  margin-top: 8px;
  background: rgb(5 29 67 / 70%);
  border: 1px solid rgb(65 150 218 / 18%);
  border-radius: 4px;
}
.tracking-history header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.tracking-history header strong {
  color: #46ccff;
  font-size: 10px;
}
.tracking-history time,
.tracking-history small,
.tracking-history-empty {
  color: #668bac;
  font-size: 9px;
}
.tracking-history p {
  margin: 8px 0;
  color: #b9d3e7;
  font-size: 10px;
  line-height: 1.6;
}
.button-secondary {
  color: #94b7d2 !important;
  background: transparent !important;
}
@media (max-width: 680px) {
  .tracking-form-grid {
    grid-template-columns: 1fr;
  }
  .tracking-form-wide {
    grid-column: auto;
  }
}
.rating-dialog {
  width: min(650px, 100%);
  max-height: calc(100vh - 60px);
  padding: 22px;
  overflow-y: auto;
}
.rating-dialog__intro,
.city-project-summary {
  margin: 16px 0;
  color: #8baec9;
  font-size: 11px;
  line-height: 1.7;
}
.rating-mode-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.rating-mode-switch button {
  min-height: 38px;
  color: #8caec9;
  background: rgb(7 39 84 / 75%);
  border: 1px solid rgb(67 151 217 / 22%);
  border-radius: 4px;
  cursor: pointer;
}
.rating-mode-switch button.active {
  color: #e6f8ff;
  background: rgb(19 119 207 / 28%);
  border-color: rgb(75 198 252 / 52%);
}
.rating-threshold-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 13px;
}
.rating-threshold-grid label,
.rating-threshold-grid > div {
  padding: 11px;
  background: rgb(7 39 84 / 65%);
  border: 1px solid rgb(67 151 217 / 18%);
  border-radius: 4px;
}
.rating-threshold-grid span {
  display: block;
  margin-bottom: 7px;
  color: #769cbb;
  font-size: 10px;
}
.rating-threshold-grid input {
  width: 100%;
  height: 31px;
  padding: 0 8px;
  color: #e1f5ff;
  background: #061f46;
  border: 1px solid rgb(77 173 235 / 28%);
  border-radius: 3px;
  outline: none;
}
.rating-threshold-grid strong {
  color: #c5dfef;
  font-size: 10px;
  font-weight: 500;
}
.rating-threshold-grid.disabled {
  opacity: 0.55;
}
.rating-score-help {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 13px;
  padding: 12px;
  color: #7299b8;
  background: rgb(5 31 70 / 52%);
  border-radius: 4px;
  font-size: 10px;
}
.rating-score-help b {
  color: #b9d8ea;
}
.rating-rule-error {
  margin: 10px 0 0;
  color: #ff7890;
  font-size: 10px;
}
.secondary-action {
  color: #8db5d0 !important;
  background: rgb(8 52 101 / 50%) !important;
  box-shadow: none !important;
}
.city-project-dialog {
  width: min(980px, 100%);
  max-height: calc(100vh - 60px);
  padding: 22px;
  overflow-y: auto;
}
.city-project-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.city-project-card {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  padding: 14px;
  color: inherit;
  background: rgb(7 39 84 / 68%);
  border: 1px solid rgb(67 151 217 / 18%);
  border-radius: 5px;
  text-align: left;
  cursor: pointer;
}
.city-project-card:hover {
  background: rgb(14 74 135 / 70%);
  border-color: rgb(75 184 241 / 38%);
}
.city-project-card > div strong,
.city-project-card > div small {
  display: block;
}
.city-project-card > div strong {
  overflow: hidden;
  color: #dceef8;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.city-project-card > div small {
  margin-top: 5px;
  color: #7198b8;
  font-size: 9px;
}
.city-project-card dl {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: 1.4fr 1fr 0.8fr;
  gap: 8px;
  margin: 2px 0 0;
}
.city-project-card dl div {
  min-width: 0;
  padding: 8px;
  background: rgb(3 25 59 / 48%);
}
.city-project-card dt {
  color: #587f9f;
  font-size: 8px;
}
.city-project-card dd {
  overflow: hidden;
  margin: 4px 0 0;
  color: #a9c6d9;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Desktop readability: keep the dense dashboard legible on large screens. */
.filter-bar {
  padding: 15px 16px;
}
.search-field,
.dashboard-select,
.search-button,
.filter-button {
  min-height: 42px;
}
.search-field input,
.dashboard-select,
.search-button,
.filter-button {
  font-size: 13px;
}
.search-field input::placeholder {
  color: #7195b6;
}
.filter-field > span {
  color: #89accb;
  font-size: 11px;
  font-weight: 500;
}
.metric-card {
  min-height: 98px;
  padding: 17px;
}
.metric-card div > span {
  color: #94b5d1;
  font-size: 12px;
  font-weight: 500;
}
.metric-card strong {
  font-size: 28px;
  font-weight: 700;
}
.metric-card small {
  color: #91b2ce;
  font-size: 12px;
}
.metric-card em {
  color: #7fa2bf;
  font-size: 11px;
  font-weight: 500;
}
.dashboard-grid {
  grid-template-columns: 270px minmax(620px, 1fr) 285px;
}
.alert-item {
  min-height: 59px;
  grid-template-columns: 44px 1fr 26px;
  padding: 11px 8px;
}
.alert-days {
  width: 40px;
  height: 40px;
  font-size: 17px;
}
.alert-days small {
  font-size: 10px;
}
.alert-content strong {
  color: #e0f1fc;
  font-size: 12px;
  font-weight: 600;
}
.alert-content em {
  color: #7198b8;
  font-size: 10px;
}
.alert-item > b,
.danger-count {
  font-size: 12px;
}
.mini-heading {
  color: #b4cee2;
  font-size: 13px;
  font-weight: 600;
}
.stage-row {
  grid-template-columns: 66px 1fr 24px;
  color: #86a8c4;
  font-size: 10.5px;
}
.back-button,
.map-provider button,
.map-modes button {
  min-height: 32px;
  padding: 6px 11px;
  color: #85aac9;
  font-size: 11px;
  font-weight: 500;
}
.map-legend,
.map-hint {
  color: #759bb9;
  font-size: 10.5px;
}
.area-card__head span,
.area-stats span {
  color: #7ca3c3;
  font-size: 10px;
}
.area-card__head strong {
  font-size: 16px;
}
.area-stats b {
  font-size: 15px;
}
.area-action {
  min-height: 34px;
  font-size: 11px;
}
.ranking-row > b {
  font-size: 12px;
}
.ranking-row > div span {
  color: #c1d7e8;
  font-size: 11px;
  font-weight: 500;
}
.ranking-row > strong {
  color: #d0e4f2;
  font-size: 11px;
}
.rating-donut strong {
  font-size: 22px;
}
.rating-donut small,
.rating-legend div {
  color: #91b2cd;
  font-size: 10px;
}
.chart-legend,
.axis-labels {
  color: #7fa3bf;
  font-size: 10px;
}
.month-labels {
  color: #7196b4;
  font-size: 9px;
}
.opportunity-list button {
  min-height: 68px;
}
.opportunity-list strong {
  color: #dfedf7;
  font-size: 12px;
  font-weight: 600;
}
.opportunity-list em {
  color: #7297b5;
  font-size: 10px;
}
.opportunity-list b {
  font-size: 12px;
}
.grade-badge,
.table-grade {
  font-size: 12px;
}
th,
td {
  padding: 14px 15px;
}
th {
  color: #8eafcb;
  font-size: 11px;
  font-weight: 600;
}
td {
  color: #a8c2d7;
  font-size: 11.5px;
}
td strong {
  color: #e0edf6;
  font-weight: 600;
}
.dialog-head small,
.dialog-grid span,
.dialog-section > span {
  color: #80a5c4;
  font-size: 11px;
}
.dialog-grid strong {
  font-size: 13px;
}
.dialog-section p,
.dialog-actions button {
  font-size: 12px;
}

@media (max-width: 1450px) {
  .dashboard-grid {
    grid-template-columns: 245px minmax(520px, 1fr) 260px;
  }
  .filter-field {
    min-width: 108px;
  }
}
@media (max-width: 1180px) {
  .dashboard-grid {
    grid-template-columns: 220px 1fr;
  }
  .ranking-panel {
    grid-column: 1 / -1;
    min-height: auto;
  }
  .ranking-panel {
    display: grid;
    grid-template-columns: 1fr 290px;
  }
  .ranking-panel .panel-heading {
    grid-column: 1 / -1;
  }
  .rating-block {
    border-top: 0;
    border-left: 1px solid rgb(70 143 211 / 12%);
    padding-left: 16px;
  }
  .filter-bar {
    flex-wrap: wrap;
  }
  .search-field {
    min-width: 100%;
  }
}
@media (max-width: 900px) {
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .alert-panel,
  .map-panel {
    min-height: auto;
  }
  .map-body {
    height: 470px;
  }
  .ranking-panel {
    grid-column: auto;
  }
  .lower-grid {
    grid-template-columns: 1fr;
  }
  .daily-additions-body {
    grid-template-columns: 1fr;
  }
  .daily-date-strip {
    grid-template-columns: repeat(7, minmax(92px, 1fr));
    overflow-x: auto;
    border-right: 0;
    border-bottom: 1px solid rgb(65 150 222 / 17%);
  }
  .daily-date-strip button {
    border-right: 1px solid rgb(65 150 222 / 10%);
    border-bottom: 0;
  }
  .daily-date-strip button.active {
    box-shadow: inset 0 -3px #42cfff;
  }
  .daily-project-item {
    grid-template-columns: 30px minmax(220px, 1fr) minmax(125px, 0.45fr) 18px;
  }
  .daily-project-deadline {
    display: none;
  }
}
@media (max-width: 620px) {
  .dashboard-heading,
  .heading-actions {
    align-items: stretch;
  }
  .heading-actions {
    width: 100%;
  }
  .heading-actions > * {
    flex: 1;
  }
  .metric-grid {
    grid-template-columns: 1fr;
  }
  .filter-field {
    min-width: calc(50% - 5px);
    flex: 1;
  }
  .search-button,
  .filter-button {
    flex: 1;
  }
  .map-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
    padding: 13px;
  }
  .map-modes {
    width: 100%;
  }
  .map-modes button {
    flex: 1;
  }
  .map-body {
    height: 430px;
  }
  .area-card {
    right: 8px;
    width: 190px;
  }
  .ranking-panel {
    display: block;
  }
  .rating-block {
    padding: 8px 0 18px;
    border-top: 1px solid rgb(70 143 211 / 12%);
    border-left: 0;
  }
  .dialog-grid {
    grid-template-columns: 1fr;
  }
  .project-overlay {
    padding: 12px;
  }
  .ai-rating-dialog {
    padding: 15px;
  }
  .ai-rating-scope,
  .ai-rating-summary {
    align-items: stretch;
    flex-direction: column;
  }
  .ai-rating-summary strong {
    margin-left: 0;
  }
  .ledger-pagination {
    flex-wrap: wrap;
    justify-content: center;
  }
  .daily-additions-heading {
    align-items: flex-start;
    gap: 8px;
  }
  .daily-project-item {
    grid-template-columns: 28px minmax(0, 1fr) 16px;
  }
  .daily-project-amount {
    display: none;
  }
}
</style>
