# 外部证据登记

核查日：2026-09-13。以下为已阅读的公开一手研究页面、作者论文和供应商官方说明。产品页面的当前日期不是历史投资证据；供应商声明不替代实测。这里只保存支持结论的简述与链接，不复制全文。

| ID | 来源 | 支持的判断 | 不能据此推导 |
|---|---|---|---|
| E01 | [Asness / Frazzini / Pedersen：Quality Minus Junk，2018 页面](https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk) | 质量特征值得纳入因子研究 | 少量美股只做多可复制多国多空质量收益 |
| E02 | [Daniel / Moskowitz：Momentum Crashes，2016 研究介绍](https://www.aqr.com/Insights/Research/Journal-Article/Momentum-Crashes) | 动量有历史证据且会在特定环境遭遇严重反转 | 多空动量的崩溃幅度可直接套到本策略只做多股票 |
| E03 | [Bessembinder：Do Stocks Outperform Treasury Bills，ASU 研究资料](https://wpcarey.asu.edu/department-finance/faculty-research/do-stocks-outperform-treasury-bills) | 长期财富创造高度集中，集中选股需要认真评估漏掉赢家的风险 | 能事前知道赢家，或收益贡献集中就必然无效 |
| E04 | [Bailey / López de Prado：Deflated Sharpe Ratio，2014 作者论文](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) | 选模次数和非正态会影响 Sharpe 可信程度 | 通过一个统计量即可保证可实现 alpha |
| E05 | [Moreira / Muir：Volatility Managed Portfolios，NBER 2016，期刊版2017](https://www.nber.org/papers/w22208) | 简单波动管理值得作为独立对照研究 | 降风险必然提高 CAGR，或不加杠杆个股版有同样效果 |
| E06 | [Morningstar：Mind the Gap 2026](https://www.morningstar.com/business/insights/research/mind-the-gap) | 时间加权与资金加权结果不同，执行体验有衡量必要 | 全部差额都是行为错误，或系统能确定追回差额 |
| E07 | [Sharadar 订阅表](https://sharadar.com/subscribe) | 当前个人版完整历史 Bundle 标价69美元/月、499美元/年 | 税/券商行情全包，或未来价格不变 |
| E08 | [Sharadar 基本面字段及维度](https://sharadar.com/docs/fundamentals) | AR/MR 和当前日期字段语义不同，历史需按可得性选值 | 所有修订、历史日内到达时间都已完整可回放 |
| E09 | [Sharadar 证券母表](https://sharadar.com/docs/tickers) | 具有永久标识和存续信息，下载母表是快照 | 当前行业、规模字段可以任意回填历史 |
| E10 | [Sharadar 个人许可](https://sharadar.com/terms) | 个人用途与商业/机构用途范围有明确区分 | 个人订阅自动允许收费分发衍生排名 |
| E11 | [SEC EDGAR 读取接口](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | 有公开 filings/XBRL、bulk 与更新机制 | 官方原始事实等于已整理完毕的研究级 PIT 数据库 |
| E12 | [FRED：ALFRED 接口说明](https://fred.stlouisfed.org/docs/api/fred/alfred.html) | 可处理宏观历史修订/vintage | 任意当前 FRED 序列都可直接用于历史决策 |
| E13 | [IBKR：Unavailable Historical Data](https://ibkrcampus.com/docs/web-api/v1/endpoints/market-data/unavailable-historical-data) | 到期期权和停止交易证券等存在历史供给限制 | 当前可调用券商工具就代表有全历史研究数据 |
| E14 | [Alpha Vantage：API 文档](https://www.alphavantage.co/documentation/) | 有预测及修正接口；公开所列请求参数未展示任意历史 as-of 查询 | 已经满足逐日多年共识快照的严格需求 |
| E15 | [Alpha Vantage：支持与额度](https://www.alphavantage.co/support/) | 常规免费档25次请求/日 | 本账户一定有付费或特殊项目额度 |
| E16 | [ORATS：Options Data API](https://orats.com/data-api) | Delayed 档199美元/月，有历史及 near-EOD 数据 | 基础股票研究必须采购，或 mid/拟合价都能真实成交 |

## 核查中需要特别防止的误读

Morningstar 同页 Executive Summary 将 8.7%/9.9%用于总体基金与 ETF，而部分 Key Findings 文案写成 US stock funds；同页明确的美股类别数为12.8%/13.3%。为避免把范围矛盾传进模型，本报告只引用其方法与定性结论，不用这些数字作为 VITALIS 可赚收益的输入。

检索到的旧 Sharadar/Nasdaq 页面和当前 Sharadar 直连产品在接口、价格、字段名及历史档位上可能不同。当前采购依据 E07，字段依据实际下载与 E08 的映射；不根据旧博客认定最新价格或授权。

## 还没有的关键证据

没有 VITALIS 净值/交易序列、正式 PIT 全量验收、样本外结果、LEAPS 真实历史成交、用户税务/风险约束、用户当前数据权限、付费客户与商用数据报价。任何人据这些文档进行下一步评估时，都应沿用这些“未知”，而非把文档完整度当成果成熟度。

后续状态更新：用户已将回撤研究上限定为约30%、IBKR留待后续。公开示例接口已实际测试：AAPL价格/ARQ财务样本通过，QQQ请求403；详见[访问元数据](../prototype/free-data-check.json)。这不等于拥有完整历史或私有订阅权限，其他缺失证据维持不变。

P001更新：Yahoo公开历史数据已实际下载并以固定规则完成样本模拟。[Yahoo官方调整价说明](https://help.yahoo.com/kb/SLN28256.html)支持其调整收盘价包含分红与拆股的口径；本项目适配器记录所有请求、原始响应哈希和事件。已做同源桥接、会计核对及离线复现，不等同于独立数据审计。详见[样本报告](../prototype/p001-results.md)；原先“没有任何交易/净值序列”状态已更新，正式PIT样本外、质量和LEAPS证据仍缺失。

P002更新（2026-09-13）：[Sharadar价格口径](https://sharadar.com/docs/stocks)、[公司行动字段](https://sharadar.com/docs/actions)及E08配合实际公开AAPL请求，证实样本字段和部分交叉一致性。2020–2025请求返回2021-09-13起价格，共1081日，缺427日；17次分红无超限差异。该结果不能推断有全部历史/全市场权限。[苹果官方公告](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/)确认2020-08-31开始4:1拆股调整交易，匹配Yahoo事件；其他企业行动与真实支付/结算时点未验收。[P002结果与溯源](../prototype/p002-results.md)、[接入合同](../prototype/historical-data-contract.md)。AR过滤可运行，不等于17份披露已逐份验原文，更不等于全池质量策略已通过。

接入/存储核查（2026-09-13）：[Sharadar query](https://sharadar.com/docs/getting-started)说明默认10000行及limit/skip；[FAQ](https://sharadar.com/docs/faqs)说明bulk、稳定标识、历史SIC与部分并购对价语义，并明确最新交易所不等于历史交易所。所查页未明确账号频率/并发额度，仍待确认。[SEC](https://www.sec.gov/about/developer-resources)用户合计10请求/秒限制不能按机器重复使用。[IBKR一般pacing](https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations/introduction)与[≤30秒bar限制](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-data-limitations/pacing-violations-for-small-bars-30-secs-or-less)分属不同约束，不可混写日频统一额度。

[DuckDB Parquet文档](https://duckdb.org/docs/lts/data/parquet/overview)支持嵌入式查询的技术选择，[SQLite WAL](https://www.sqlite.org/wal.html)限定单主机且writer仍单个。文档能力不等于项目已部署、压测或做到跨进程限流；实施状态及待验收测试见[本地数据设计](../prototype/local-data-architecture.md)。
