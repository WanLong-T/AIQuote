# 模块2：AI成本测算

本目录由模块2负责人 郭之翰 独立维护。

- `frontend/Module2Page.vue`：成本测算页面与大模型配置界面。
- `backend/`：模块2后续新增的独立接口、计算适配器和测试。
- `docs/`：模块2清单样例与业务资料。
- `data/江苏省/清单/房屋建筑与装饰工程/`：已纳入版本控制的江苏省 2024 房屋建筑与装饰工程清单库（471 条）；江苏省定额价格库尚待补充。
- 当前计算脚本暂存于 `platform/scripts/cost-engine.py` 和 `platform/scripts/export-cost-report.py`，后续抽离时应通过模块接口适配，不要让页面直接依赖脚本路径。

模块接口统一使用 `/api/cost/...` 命名空间。
