# 14-taximeter（打车计价）

Taximeter — 起步价 + 里程价 + 低速时长费（夜间加价系数）

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4300 |
| API | http://localhost:9300 |

## 主链

录行程里程与低速时长 → 拆解车费 → 行程单

## 节假日系数

- 维护服务日期与系数（系数必须大于零）：`GET/POST /api/holidays`、`PUT /api/holidays/{id}`、`POST /api/holidays/{id}/deactivate|activate`；同一日期不允许两条启用记录，冲突时 409 并点名两条记录编号。
- 打表提交 `service_date`（YYYY-MM-DD）：命中启用日期时，在夜间处理之后再乘该系数，起步/里程/低速/应付分别四舍五入到分；不提交或不命中则结果与不加系数完全一致。
- 已写入的 `calc_runs` 记录保留当时乘后数字与所用系数，事后修改该日系数不回写历史记录。

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
