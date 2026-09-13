# 数据源接入：用户动作与工程责任

核查日2026-09-13。目标保持：总本金20万–40万美元、净收益优先超过QQQ、回撤研究上限约30%、数据费总计≤1000美元/年。本次没有采购、注册新账户或连接用户券商。

## 现在需要用户做什么

| 来源 | 用户动作 | 用途与顺序 |
|---|---|---|
| 已有授权历史文件 | 若已有，放在本地`data/authorized/`，附来源、权益和字段说明 | 优先验收，避免重复订阅 |
| Sharadar | 没有历史权益时，注册自己的账号获取key；先确认Full History Bundle范围及限额，再决定订阅 | 核心候选：股票历史、QQQ、AR财务、证券母表、行动及退出者 |
| SEC EDGAR | 无需订阅/API key；开始采集时为User-Agent提供真实联系邮箱，保存在本地配置 | 免费披露抽查与前向归档，不替代整理好的全市场PIT库 |
| Yahoo公开样本 | 现有样本无需注册 | 工程诊断与交叉核对，不作为正式历史股票池主库 |
| IBKR（用户所说ABKR） | **现在无需Gateway或购买行情** | 后续读持仓、现金、当前报价；不补完整退市历史 |
| 宏观、预测、期权及新闻 | 当前无需注册/订阅 | 对应模块获证后才评估，计入同一预算 |

Sharadar注册可取得key，但不代表获得完整历史权益。当前Full History Bundle标价69美元/月或499美元/年；5年29美元/月档不是完整历史。若先月付验收再单独年付、无抵扣，基础首年568美元，税及其他数据费仍需计入1000美元上限。先确认样本再选支付周期，不假设退款或抵扣。[认证](https://sharadar.com/docs/auth)、[订阅范围与价格](https://sharadar.com/subscribe)。

需要确认的权益：可用表、历史起点与退出者、每秒/滚动/每日配额、并发上限、bulk限制及更新频次、个人存储/备份许可、订阅结束后的保存/使用权限、税费。公开query/auth/FAQ页未明确给出Sharadar账号频率或并发额度，待账号资料或供应商确认；未找到不等于无限制。

账号密码和key不要粘贴到聊天或写进仓库。可在本地准备`SHARADAR_API_KEY`环境变量；**当前公开样本CLI尚未读取此变量**，私有适配器实现后才接入。供应商原文件不用用户手工修改；工程负责字段映射与验收。

## IBKR Gateway何时建立

进入个人组合前向影子阶段再配置。采用TWS Socket API时，TWS与IB Gateway均可作为本地连接端，常驻只读采集可选择Gateway；不必同时运行两者。Client Portal Web API是另一条路径，当前不并行开发两套。

用户安装官方Stable版、登录及完成2FA，首次优先paper环境联通验证。启用Socket API、核对实际端口及独立client ID、只信任本地地址，**保持Read-Only API开启**。官方下单教程要求关闭只读是为了交易，不适用于本工程只读范围。[配置入口](https://www.interactivebrokers.com/docs/tws-api/doc/tws-settings/introduction)、[连接说明](https://www.interactivebrokers.com/docs/tws-api/doc/connectivity/establishing-an-api-connection)。

工程核对账户环境与只读权限、持仓/现金回调、行情live/delayed类型、重连及重复请求。能看到持仓不代表订阅了API实时行情；行情权限按实际需求另核查、费用计入预算。当前官方API要求列明IBKR Pro账户、TWS/Gateway/API版本与Python最低3.11；接入SDK时单独锁兼容环境，现有离线原型最低Python3.9不因此被误报。[API要求](https://www.interactivebrokers.com/docs/tws-api/doc/notes-limitations/requirements)、[行情限制](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-live/live-data-limitations)。

需记录每日重启、每周重新认证、笔记本休眠及会话冲突，不能承诺永久无人值守登录。当前官方周认证周期从周一开始，需准备人工重新登录。[重认证说明](https://www.interactivebrokers.com/docs/tws-api/doc/tws-settings/daily-weekly-reauthentication)。

## 来源限制登记

| 来源/端点 | 已核查官方约束 | 项目初始策略，不是供应商额度 |
|---|---|---|
| Sharadar REST/bulk | query默认10000行、limit/skip分页；bulk历史匹配订阅。频率/并发/每日额度待确认 | 单并发，REST最多1次/秒、200次/UTC日；初始全量优先bulk，权益更低则下调 |
| SEC EDGAR | 每用户跨机器合计≤10请求/秒，需识别User-Agent及公平访问 | 单并发、2次/秒；真实联系标识，批量/增量优先 |
| Yahoo chart样本 | 未找到可作承诺的该端点官方额度/SLA | 单并发、最多0.5次/秒，只显式样本采集 |
| IBKR一般Socket请求 | 每秒market data lines÷2；默认100 lines对应50次/秒；活跃订阅额度另计 | 暂停用；后续一般请求5次/秒，报价订阅最多10个；按实际权益下调 |
| IBKR ≤30秒历史bar | 相同请求15秒内、同合约/交易所/tick类型2秒内≥6次、10分钟>60次等触发限制；BID_ASK双计 | 不在当前日频范围；不能把这些数当日bar通用上限 |

依据：[Sharadar query](https://sharadar.com/docs/getting-started)、[bulk/FAQ](https://sharadar.com/docs/faqs)、[SEC公平访问](https://www.sec.gov/about/developer-resources)、[IBKR一般pacing](https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations/introduction)、[小bar限制](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-data-limitations/pacing-violations-for-small-bars-30-secs-or-less)。

配置提案见[`config/data-source-policy.json`](../../config/data-source-policy.json)，**尚未接入现有CLI**。后续由统一调度器实施来源/账号/端点窗口约束，登记实际限流响应。每秒频率、滚动/每日次数、并发、活跃订阅与历史深度分开验；sleep不能替代全部限制，不用换账号/IP规避额度。

## 完成标准

用户提供合法权益与本地配置；工程负责下载、分页、恢复、缓存、覆盖与时点核验。具体字段见[历史接入清单](historical-data-contract.md)，运行设计见[本地数据架构](local-data-architecture.md)。订阅存在不等于验收通过，只有合格本地数据版本才能推进历史池动量与质量闭环。
