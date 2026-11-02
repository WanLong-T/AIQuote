# 多人协作与前端装配方案

## 目录所有权

| 区域 | 负责人 | 日常修改范围 |
| --- | --- | --- |
| 模块1 | 项目情报负责人 | `modules/module-1/**` |
| 模块2 | 成本测算负责人 | `modules/module-2/**` |
| 模块3 | 结果分析负责人 | `modules/module-3/**` |
| 模块4 | 模拟分析负责人 | `modules/module-4/**` |
| 主框架 | 集成人员 | `platform/**`、公共协议 |

## 为什么不会共用一个前端而混乱

四个模块仍使用同一个Vue应用和统一菜单，但业务页面源码位于四个独立目录。`platform/src/pages` 中每个文件只有一个组件引用，用于把模块页面接入总页面。模块负责人不需要同时编辑主布局或同一个大页面，因此Git冲突会显著减少。

## 分支约定

- `feat/module-1-*`
- `feat/module-2-*`
- `feat/module-3-*`
- `feat/module-4-*`
- `chore/platform-*`（仅集成人员）

每次Pull Request只包含一个模块。若同时需要主框架改动，应拆成第二个提交或第二个Pull Request。
