# 模块1：项目情报与全国项目地图

本目录由模块1负责人 高媛 独立维护。

- `frontend/`：全国项目地图、项目台账、每日新增看板、AI项目评级。
- `crawler/`：项目公告爬虫、采集数据、导入脚本和运行日志。
- 前端入口：`frontend/Module1Page.vue`。
- 当前共享接口由 `platform/scripts/serve-lan.mjs` 提供；新增接口应保持 `/api/projects/...` 命名空间。

除非修改公共协议，不要改动其他模块目录或 `platform`。需要公共改动时单独提交，由集成人员合并。
