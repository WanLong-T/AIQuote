# AIQuote 工程投标智能决策系统

这是当前可继续协作开发的半成品代码库。仓库采用单仓库分类管理，软件前端、后端、爬虫和项目资料分别存放，但不提交密码、API Key、依赖目录、构建产物及大体量采集结果。

## 目录结构

```text
AIQuote/
├─ platform/            主框架、公共路由、布局和API网关
├─ modules/
│  ├─ module-1/         项目情报、地图、AI评级和爬虫
│  ├─ module-2/         AI成本测算
│  ├─ module-3/         投标结果分析
│  └─ module-4/         投标模拟分析
├─ docs/                协作规范与公共参考资料
└─ README.md
```

## 本地启动

1. 复制 `platform/.env.example` 为 `platform/.env.local`，填写本机数据库和第三方服务配置。
2. 安装 Node.js 22.12 以上版本和 MySQL。
3. 在仓库根目录安装共享依赖并启动服务：

```bash
npm install
npm run build
npm run serve:lan
```

开发模式前端使用：

```bash
npm run dev
```

正式数据接口默认运行在 `http://localhost:9000`，前端开发服务默认运行在 `http://localhost:9001`。

## 爬虫

爬虫代码位于 `crawler`，依赖见 `crawler/requirements.txt`。爬虫产生的 `数据`、`日志` 和 `logs` 目录不进入Git；数据库密码通过环境变量 `BIDDING_DB_PASSWORD` 提供。

## 协作约定

- `main` 只保存可运行版本，不直接在 `main` 上开发。
- 每项工作创建独立分支，例如 `feat/module1-dashboard`、`feat/cost-analysis`、`fix/project-import`。
- 提交前至少运行 `npm run typecheck` 和 `npm run build`。
- 通过 Pull Request 合并，说明改动内容、验证方式和数据库变更。
- 禁止提交 `.env.local`、数据库密码、AI Key、真实账号凭据及本地加密配置。

## 当前技术栈

- 前端：Vue 3、TypeScript、Quasar、ECharts
- 后端：Node.js、MySQL
- 数据与计算：Python
- AI：兼容 OpenAI Chat Completions 的模型接口

