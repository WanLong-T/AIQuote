# AIQuote 前端目录说明

本文档对应 `E:\AIQuote\frontend` 当前实际目录，说明每个业务源码、配置文件和脚本的用途。

项目采用 Vue 3 + Quasar CLI/Vite + TypeScript + CSR，使用 npm workspace 管理多个独立应用。Portal 只负责导航和 iframe 挂载，四个业务模块各自独立启动。

## 1. 顶层目录

```text
frontend/
├─ apps/                         # 应用入口
│  └─ portal/                    # 总入口，默认端口 3000
├─ packages/                     # 业务模块和共享包
│  ├─ national-project-map/      # 全国项目地图，默认端口 3001
│  ├─ ai-cost-estimation/        # AI 成本测算，默认端口 3002
│  ├─ bid-template-analysis/     # 投标模板分析，默认端口 3003
│  ├─ bid-result-analysis/       # 投标结果分析，默认端口 3004
│  └─ shared/                    # 公共组件、样式和通用类型
├─ scripts/                      # 根目录辅助脚本
├─ package.json                  # 根 workspace 配置和启动命令
├─ package-lock.json             # npm 依赖锁定文件
├─ pnpm-workspace.yaml           # pnpm workspace 配置文件（当前实际使用 npm）
├─ tsconfig.json                 # 根 TypeScript 配置
├─ eslint.config.js              # ESLint 配置
├─ .prettierrc.json              # Prettier 配置
├─ .editorconfig                 # 编辑器基础格式配置
└─ .gitignore                    # Git 忽略规则
```

## 2. 根目录文件

| 文件                  | 作用                                                                                                                                                                                              |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `package.json`        | 声明根 workspace、公共依赖和启动命令。`dev` 默认启动 Portal；`dev:all` 同时启动五个服务；`dev:map`、`dev:ai`、`dev:template`、`dev:result` 分别启动单个业务模块；`typecheck` 执行全项目类型检查。 |
| `package-lock.json`   | npm 安装结果的锁定文件，保证团队依赖版本一致。不要手工编辑。                                                                                                                                      |
| `pnpm-workspace.yaml` | pnpm 的 workspace 配置文件。当前项目存在它，但因为根目录有 `package-lock.json`，实际启动和安装以 npm workspace 为准。                                                                             |
| `tsconfig.json`       | 根 TypeScript 配置，覆盖 `apps/**/*` 和 `packages/**/*`，并配置 `@aiquote/shared` 路径别名。                                                                                                      |
| `eslint.config.js`    | ESLint flat config，启用 Vue、TypeScript、Quasar 推荐规则，并忽略 `node_modules`、`dist`、`.quasar`。                                                                                             |
| `.prettierrc.json`    | Prettier 的代码格式规则。                                                                                                                                                                         |
| `.editorconfig`       | 统一缩进、换行符和文件末尾格式。                                                                                                                                                                  |
| `.gitignore`          | 忽略依赖、构建产物、本地 `.env` 和 Quasar 生成目录等文件。                                                                                                                                        |
| `scripts/dev-all.mjs` | 使用 Node `child_process.spawn` 并行拉起 Portal 和四个业务模块；按 Ctrl+C 时统一停止子进程。                                                                                                      |
| `README.md`           | 项目结构、启动方式、端口、模块边界和文件职责说明。                                                                                                                                                |

## 3. `apps/portal` 总入口

Portal 是总入口，只做模块导航和 iframe 挂载，不放业务模块的 API 或业务状态。

### 3.1 根文件

| 文件                           | 作用                                                                                                                            |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `apps/portal/package.json`     | Portal workspace 的依赖和命令。`dev` 使用 `quasar dev`，`build` 使用 `quasar build`。                                           |
| `apps/portal/quasar.config.ts` | Quasar CLI/Vite 配置：启用 hash 路由、全局 SCSS、Material Icons、监听 `0.0.0.0`，默认端口 3000；端口可由 `VITE_DEV_PORT` 覆盖。 |
| `apps/portal/index.html`       | Portal 的 HTML 壳和页面标题。`<!-- quasar:entry-point -->` 由 Quasar CLI 替换为实际入口。不要用普通静态服务器直接打开此文件。   |
| `apps/portal/env.d.ts`         | 为 `import.meta.env` 声明 Portal 使用的环境变量类型。                                                                           |
| `apps/portal/.env.example`     | Portal 环境变量模板：自身端口和四个 iframe 模块地址。复制为 `.env` 后再按机器地址修改；真实 `.env` 不提交。                     |
| `apps/portal/tsconfig.json`    | Portal 专用 TypeScript 配置，包含 `src` 和环境声明，并指向共享包类型。                                                          |

### 3.2 `apps/portal/src`

| 文件                             | 作用                                                                                                                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/App.vue`                    | Portal 根组件，提供 Quasar 的 `q-layout`、`q-page-container`，并渲染当前路由的页面。                                                                                            |
| `src/router/index.ts`            | Portal 路由。`/` 是导航首页，`/map`、`/ai`、`/template`、`/result` 对应四个模块，未知路径重定向到首页。使用 hash 路由。                                                         |
| `src/config/modules.ts`          | Portal 模块注册表。保存模块 key、显示名称、描述、图标、路由和 iframe URL；URL 优先读取环境变量，没有配置时使用 localhost 默认端口。`moduleEntryUrl` 负责拼接模块的 `/#/` 入口。 |
| `src/components/ModuleFrame.vue` | 模块容器组件，显示当前模块标题、返回 Portal 的链接，并用 iframe 加载模块 dev server。                                                                                           |
| `src/pages/index.vue`            | Portal 首页界面，展示系统概览、四个模块卡片和进入模块的导航。这里只调用模块注册表，不写业务 API。                                                                               |
| `src/pages/module.vue`           | 根据路由传入的 `moduleKey` 查找模块配置，并复用 `ModuleFrame.vue`。                                                                                                             |
| `src/css/app.scss`               | Portal 全局样式入口，加载共享颜色变量、布局样式，并设置全局盒模型、页面高度和字体。                                                                                             |

Portal 默认嵌入地址：

| 模块         | Portal 路径 | 默认 iframe 地址           |
| ------------ | ----------- | -------------------------- |
| 全国项目地图 | `/map`      | `http://localhost:3001/#/` |
| AI 成本测算  | `/ai`       | `http://localhost:3002/#/` |
| 投标模板分析 | `/template` | `http://localhost:3003/#/` |
| 投标结果分析 | `/result`   | `http://localhost:3004/#/` |

## 4. 四个业务模块的共同结构

以下四个目录都是独立的 Quasar 应用：

- `packages/national-project-map`
- `packages/ai-cost-estimation`
- `packages/bid-template-analysis`
- `packages/bid-result-analysis`

每个模块都只能访问自己的 `src` 和 `packages/shared`，不能直接 import 其他模块的内部文件。后续接后端时，页面通过本模块 `src/api/` 调用接口适配层，不在页面中直接写请求。

每个模块的通用文件职责如下：

| 相对文件                 | 作用                                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `.env.example`           | 保存该模块的端口和后端 API Base URL 占位变量。                                                                |
| `env.d.ts`               | 为该模块的 `import.meta.env` 变量提供 TypeScript 类型。                                                       |
| `index.html`             | Quasar HTML 壳，保存模块标题和 Quasar 入口占位符。                                                            |
| `package.json`           | 该模块的 workspace 名称、依赖以及 `dev`、`build`、`typecheck` 命令。                                          |
| `quasar.config.ts`       | 该模块的 Quasar/Vite 配置。默认监听 `0.0.0.0`，分别使用 3001、3002、3003、3004；端口由 `VITE_DEV_PORT` 覆盖。 |
| `tsconfig.json`          | 该模块的 TypeScript 配置，并为 `@aiquote/shared` 配置路径。                                                   |
| `src/App.vue`            | 模块根组件，只渲染当前模块的 `router-view`。                                                                  |
| `src/router/index.ts`    | 模块自己的 hash 路由和详情页路由。                                                                            |
| `src/css/app.scss`       | 加载共享主题变量和布局，并设置全局基础样式。                                                                  |
| `src/api/index.ts`       | 当前模块的接口类型、函数签名和本地假数据实现。所有函数都标注了 `TODO(api)`，以后替换这里即可接后端。          |
| `src/mock/.gitkeep`      | 保留 mock 目录结构的占位文件；当前不启动 mock 服务端。                                                        |
| `src/pages/index.vue`    | 模块首页的界面骨架。                                                                                          |
| `src/pages/*-detail.vue` | 模块详情页占位界面，从 Vue Router 参数中读取详情 ID。                                                         |

## 5. 全国项目地图模块

目录：`packages/national-project-map`

| 文件                           | 作用                                                                                                                                                        |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.env.example`                 | `VITE_DEV_PORT=3001` 和 `VITE_NATIONAL_PROJECT_MAP_API_BASE` 占位变量。                                                                                     |
| `src/pages/index.vue`          | 全国项目地图首页骨架。                                                                                                                                      |
| `src/pages/project-detail.vue` | 项目详情占位页，读取 `/projects/:projectId` 参数。                                                                                                          |
| `src/router/index.ts`          | 路由 `/`、`/projects/:projectId` 和未知路由重定向。                                                                                                         |
| `src/api/index.ts`             | 定义 `ProjectMapQuery`、`ProjectMapPoint`、`ProjectDetail`；提供 `listProjectMapPoints(query)` 和 `getProjectDetail(projectId)`。当前返回本地项目点假数据。 |

## 6. AI 成本测算模块

目录：`packages/ai-cost-estimation`

| 文件                            | 作用                                                                                                                                                               |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `.env.example`                  | `VITE_DEV_PORT=3002` 和 `VITE_AI_COST_ESTIMATION_API_BASE` 占位变量。                                                                                              |
| `src/pages/index.vue`           | AI 成本测算首页骨架。                                                                                                                                              |
| `src/pages/estimate-detail.vue` | 测算详情占位页，读取 `/estimates/:estimateId` 参数。                                                                                                               |
| `src/router/index.ts`           | 路由 `/`、`/estimates`、`/estimates/:estimateId` 和未知路由重定向。                                                                                                |
| `src/api/index.ts`              | 定义测算查询、摘要、详情、输入和结果类型；提供 `listEstimates(query)`、`getEstimateDetail(estimateId)`、`calculateEstimate(input)`。当前使用本地假数据和前端计算。 |

## 7. 投标模板分析模块

目录：`packages/bid-template-analysis`

| 文件                            | 作用                                                                                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.env.example`                  | `VITE_DEV_PORT=3003` 和 `VITE_BID_TEMPLATE_ANALYSIS_API_BASE` 占位变量。                                                                                       |
| `src/pages/index.vue`           | 投标模板分析首页骨架。                                                                                                                                         |
| `src/pages/analysis-detail.vue` | 模板分析详情占位页，读取 `/analyses/:analysisId` 参数。                                                                                                        |
| `src/router/index.ts`           | 路由 `/`、`/analyses`、`/analyses/:analysisId` 和未知路由重定向。                                                                                              |
| `src/api/index.ts`              | 定义模板分析查询、摘要和详情类型；提供 `listTemplateAnalyses(query)`、`getTemplateAnalysis(analysisId)`、`analyzeTemplate(fileName)`。当前返回本地分析假数据。 |

## 8. 投标结果分析模块

目录：`packages/bid-result-analysis`

| 文件                          | 作用                                                                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `.env.example`                | `VITE_DEV_PORT=3004` 和 `VITE_BID_RESULT_ANALYSIS_API_BASE` 占位变量。                                             |
| `src/pages/index.vue`         | 投标结果分析首页骨架。                                                                                             |
| `src/pages/result-detail.vue` | 投标结果详情占位页，读取 `/results/:resultId` 参数。                                                               |
| `src/router/index.ts`         | 路由 `/`、`/results`、`/results/:resultId` 和未知路由重定向。                                                      |
| `src/api/index.ts`            | 定义投标结果查询、摘要和详情类型；提供 `listBidResults(query)`、`getBidResult(resultId)`。当前返回本地结果假数据。 |

## 9. `packages/shared` 共享包

共享包不保存具体业务逻辑，不保存某一个模块的状态；只放可以被多个模块复用的组件、样式和契约类型。

| 文件                                  | 作用                                                                                                                                           |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `packages/shared/package.json`        | 共享包的名称、入口和 Vue peer dependency。                                                                                                     |
| `src/index.ts`                        | 统一导出 API 类型和三个公共 Vue 组件。其他包从 `@aiquote/shared` 使用这些导出。                                                                |
| `src/types/api.ts`                    | 通用接口契约：`PaginationParams` 分页参数、`PaginatedData<T>` 分页数据、`ApiResponse<T>` 统一响应、`ApiError` 错误结构、`DateRange` 日期范围。 |
| `src/components/ModulePageHeader.vue` | 公共模块标题组件，支持眉标题、标题、描述和 actions 插槽。                                                                                      |
| `src/components/StatusBadge.vue`      | 公共状态标签组件，支持 info、success、warning、danger、muted 五种颜色。                                                                        |
| `src/components/EmptyState.vue`       | 公共空状态组件，显示标题和可选描述。                                                                                                           |
| `src/styles/tokens.scss`              | 公共 CSS 变量，包括背景、面板、文字、强调色和边框色。                                                                                          |
| `src/styles/layout.scss`              | 公共模块页面布局，包括最小高度、内边距、内容最大宽度和背景渐变。                                                                               |

## 10. 环境变量和端口

默认端口：

```text
Portal                 3000
全国项目地图           3001
AI 成本测算            3002
投标模板分析           3003
投标结果分析           3004
```

例如需要把地图模块改到 3011，可以在 `packages/national-project-map/.env` 中写：

```env
VITE_DEV_PORT=3011
```

Portal 中对应的 iframe 地址也要改为实际地址，例如在 `apps/portal/.env` 中写：

```env
VITE_NATIONAL_PROJECT_MAP_URL=http://localhost:3011
```

局域网预览时，不能把其他人的浏览器中的 `localhost` 当成开发机。应把 Portal 和模块都监听在 `0.0.0.0`，并把 Portal 的模块 URL 改成开发机局域网 IP。

## 11. 启动和检查

在 `E:\AIQuote\frontend` 执行：

```powershell
npm install

# 只启动 Portal
npm run dev

# 或明确启动 Portal
npm run dev:portal

# 同时启动 Portal 和四个模块
npm run dev:all

# 单独启动模块
npm run dev:map
npm run dev:ai
npm run dev:template
npm run dev:result
```

打开：

```text
http://localhost:3000/
```

建议检查：

```powershell
npm run typecheck
npm run lint:check
npm --workspace @aiquote/portal run build
```

如果 3000 页面空白，先确认启动命令是在 `E:\AIQuote\frontend` 执行的，并关闭旧的 Node/Vite/Quasar 进程；不要用普通静态服务器或直接双击 `apps/portal/index.html`，因为其中的 `quasar:entry-point` 需要由 Quasar CLI 处理。Portal 页面需要四个模块服务时，还要同时启动对应的模块端口。

## 12. 不应手工修改或提交的目录

以下目录是依赖安装、构建或 Quasar 自动生成的内容，不属于业务源码：

| 目录                         | 作用                                                                                                                                    |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `node_modules/`              | npm 安装的依赖。删除后可以通过 `npm install` 恢复。                                                                                     |
| 各 workspace 下的 `dist/`    | Quasar/Vite 构建产物。                                                                                                                  |
| 各 workspace 下的 `.quasar/` | Quasar CLI 生成的临时入口、类型声明和构建缓存。                                                                                         |
| 根目录遗留的空 `src/` 子目录 | 旧版单体前端迁移后留下的空目录，不参与当前 monorepo 构建；其中 `src/boot/.gitkeep` 只是保留目录的占位文件。新代码应放入对应 workspace。 |

不要把 `.env`、真实后端地址、构建产物或 `node_modules` 提交到版本库。
