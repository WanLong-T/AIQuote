# 主框架与共享运行平台

`platform` 是四个业务模块的装配层，不归某个业务模块负责人日常修改。

主要职责：

- 应用启动、菜单、主布局、全局样式与路由入口。
- 公共类型、鉴权、数据库连接和API网关。
- 将 `src/pages/*.vue` 薄入口映射到 `modules/module-X/frontend/ModuleXPage.vue`。

协作约定：

1. 模块开发人员只修改自己的 `modules/module-X`。
2. `platform/src/pages` 只保留薄入口，不在其中编写业务逻辑。
3. 菜单、公共类型或网关需要变更时，单独发起Pull Request并指定集成人员审核。
4. 模块之间通过API或共享类型通信，不互相直接修改内部组件。
