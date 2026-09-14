# 本地存储与限流采集设计

状态：2026-09-13设计决定。现有实现是不可变JSON缓存、CSV/JSON结果和显式`--offline`；下述共享目录、调度器与Parquet/DuckDB尚待实现。

## 实施进度（P004）

`vitalis.research_audit.pin_inputs()`现已实现SQLite的`snapshot`/`artifact`最小目录：实际文件SHA-256核验、原始侧录哈希比对、代码复制、运行状态与文件路径登记。历史池runner只读精确本地缓存，完成前再次核验源文件，保存输出哈希和实验登记。当前目录没有`ingestion_job`、`rate_state`、`coverage`等表，也没有协调远程worker；不可将此宣称为完整采集平台。新增`data/authorized/sharadar/derived-cache/`的校验gzip JSON快照，缓存日历、市值切片和标准化bar；键包含源哈希、规范化代码及范围。单CLI协调，尚无并发发布租约。Parquet/DuckDB继续按实测扫描/查询瓶颈逐步实施，原始zip不重拉。

## 技术选择

采用**原始文件 + Parquet/DuckDB研究层 + SQLite采集目录**。单机日频/月度决策需要按稳定证券ID、日期查询和跨截面扫描；时序持久化必需，独立TimescaleDB/InfluxDB服务不是当前前置依赖。

DuckDB支持本地Parquet读写、列选择与过滤下推，适合离线研究；实际全市场性能仍需测量。[官方说明](https://duckdb.org/docs/lts/data/parquet/overview)。SQLite保存请求/覆盖/检查点/限流/快照目录。若采用WAL，限定同主机本地磁盘，仍只有一个writer；用backup API或停写checkpoint备份，不只复制正在写的数据库文件。[SQLite WAL](https://www.sqlite.org/wal.html)。

先完成SQLite目录、采集协调与现有缓存登记；获授权样本后再做版本化Parquet和DuckDB查询，采用独立环境与版本锁、验证Python兼容性。不为准备数据搭数据库集群或云平台；只有实测容量、查询延迟、多主机写入超出单机方案时重新决策。

## 分层与数据版本

```text
显式采集 → 共享限流/任务队列 → 供应商或授权导出
                                 ↓
data/raw/<source>/<dataset>/<snapshot>/        不可变原响应/zip/原表
                                 ↓ 校验与规范化
data/normalized/<dataset>/<version>/year=YYYY/*.parquet
                                 ↓ 发布合格manifest
data/catalog.sqlite                          请求/覆盖/任务/版本目录
                                 ↓ 固定本地snapshot ID
因子 → 组合 → 账本 → QQQ/风险/成本 → decision → 实验登记
```

按dataset/version/year分区，文件内按稳定ID及日期排序；不为每只股票每个交易日制造小文件。DuckDB派生表可重建，目录必须能追溯源文件。

每个研究运行固定manifest、数据/代码/schema版本和截至时点。**研究不联网**，缺数据失败/证据不足；远程获取只由显式采集任务执行，UI刷新只查本地。现有CLIs仍允许在线初始化，应使用`--offline`重跑；后续入口变更需迁移说明。

## 增量、修订与新鲜度

初始完整历史优先授权bulk。后续按源端更新字段取增量，而不只请求最新交易日：财务、历史行动和价格可修正旧日期。设重叠窗口、去重、watermark，周期比较bulk状态/哈希，需要时追加新版本，不每天重拉全表。订阅历史与分页覆盖需验收，HTTP200不等于完整；P002缺427日是实际回归案例。

冻结研究快照不自动过期，依许可保留；更正另发版本。最新行情在收盘及供应商批次完成后采集，显示实际as-of，漏session不静默沿用。AR财务保留申报日、所属期、可得日与修订，当前母表/行业不覆盖历史。后续IBKR报价通过回调缓存，保存行情时间/接收时间/live或delayed类型；过期数据可标陈旧显示，不能驱动新建议。

请求键含来源、非秘密权益profile、dataset、规范化参数/范围/字段/schema版本，不含凭证。相同请求命中缓存，重叠范围按coverage拆缺口。缓存原始文件只追加，不覆盖历史；签名URL、API key不写日志，也不能用签名URL作数据版本。

## SQLite最小目录合同

| 表 | 内容与约束 |
|---|---|
| `source_profile` | 非秘密权益ID、官方限额证据、项目caps、核查日期、数据费用 |
| `ingestion_job` | 请求键唯一、租约/heartbeat、状态、分页/恢复检查点；跨进程合并相同任务 |
| `request_attempt` | 每次尝试时间、HTTP/供应商错误、字节数、Retry-After及耗时；失败尝试也计额度 |
| `rate_state` | 来源/profile/端点窗口计数、共享cooldown、并发租约；重启不清空限流历史 |
| `coverage` | 稳定ID/dataset/范围、预期分母、实际行数/session、缺失原因、complete/partial |
| `snapshot` / `artifact` | 版本、输入/代码/schema哈希、路径、取得时间、publication/available语义、质量状态 |

入队/额度预留/租约获取在短事务完成，网络等待不占写事务。文件先临时写入、校验后原子发布，再登记合格manifest；部分页不推进完整watermark。SQLite与文件不是跨文件原子事务，需孤儿文件扫描、临时文件检查与过期租约恢复。不能提前发布完成状态。

## 限流与失败处理

统一协调同来源/权益profile的所有worker和CLI，同时施加端点及用户/IP级约束。跨机器的SEC总上限需分配共享预算或协调，不能每台独用全部额度。

官方限额与项目低速caps分栏，按更严格者执行；未知额度待确认。429尊重Retry-After（秒数或HTTP-date），保存cooldown；没有该字段时用抖动指数退避。传输/超时及有限5xx可自动重试最多3次，401/403不自动重试。较长等待挂起任务、保存下次执行时间，不阻塞研究UI；timeout后本次尝试仍计数，不靠重启/换key逃逸。

REST显式范围/字段/limit/skip；满page继续分页，不作为完成标志。按合成主键去重，同日期多行及分页期间更新要检查；只有date排序不足以保证变化中的结果稳定。源变化则隔离/重采范围，优先不可变bulk。bulk状态/链接申请/实际下载也登记请求。分别控制频率、滚动窗口、日quota、并发、行情lines及历史depth。

## 实施验收与闭环

1. 共享目录登记现有缓存，不下载；同版本重跑远程调用0、哈希一致，离线缺口可解释。
2. 统一采集器用mock HTTP/时钟验证去重、并发/窗口额度、429/鉴权、分页截断及崩溃恢复，不消耗真实quota。
3. 实际权益确认后bulk入库，稳定ID映射、版本化Parquet、时点/行动/退出者验收，锁定环境。
4. P003冻结历史池动量基线，再加质量增量；净QQQ差、约30%回撤门槛、Ulcer/水下期、费用/换手及decision齐备。
5. 之后接IBKR只读影子组合：建议→人工决定/覆盖原因→实际持仓/成本→复盘，不自动下单。

各阶段标明已实现与待实现。缓存命中率、速度或订阅数量都不能替代收益与持有体验证据。
