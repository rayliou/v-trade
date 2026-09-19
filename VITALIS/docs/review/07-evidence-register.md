# 外部证据登记

首批核查日：2026-09-13；E18–E35增补于2026-09-19。以下为已阅读的公开一手研究页面、作者论文和供应商官方说明。产品页面的当前日期不是历史投资证据；供应商声明不替代实测。这里只保存支持结论的简述与链接，不复制全文。

| ID | 来源 | 支持的判断 | 不能据此推导 |
|---|---|---|---|
| E01 | [Asness / Frazzini / Pedersen：Quality Minus Junk，2018 页面](https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk) | 质量特征值得纳入因子研究 | 少量美股只做多可复制多国多空质量收益 |
| E02 | [Daniel / Moskowitz：Momentum Crashes，2016 研究介绍](https://www.aqr.com/Insights/Research/Journal-Article/Momentum-Crashes) | 动量有历史证据且会在特定环境遭遇严重反转 | 多空动量的崩溃幅度可直接套到本策略只做多股票 |
| E03 | [Bessembinder：Do Stocks Outperform Treasury Bills，ASU 研究资料](https://wpcarey.asu.edu/department-finance/faculty-research/do-stocks-outperform-treasury-bills) | 长期财富创造高度集中，集中选股需要认真评估漏掉赢家的风险 | 能事前知道赢家，或收益贡献集中就必然无效 |
| E04 | [Bailey / López de Prado：Deflated Sharpe Ratio，2014 作者论文](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) | 选模次数和非正态会影响 Sharpe 可信程度 | 通过一个统计量即可保证可实现 alpha |
| E05 | [Moreira / Muir：Volatility Managed Portfolios，NBER 2016，期刊版2017](https://www.nber.org/papers/w22208) | 简单波动管理值得作为独立对照研究 | 降风险必然提高 CAGR，或不加杠杆个股版有同样效果 |
| E06 | [Morningstar：Mind the Gap 2026](https://www.morningstar.com/business/insights/research/mind-the-gap) | 时间加权与资金加权结果不同，执行体验有衡量必要 | 全部差额都是行为错误，或系统能确定追回差额 |
| E07 | [Sharadar 订阅表](https://sharadar.com/subscribe) | 当前个人版完整历史（Full History）档：Fundamentals单独39美元/月（399美元/年）、Prices单独39美元/月（299美元/年）、Bundle 69美元/月（499美元/年）；5年、10年为更低档，不是同一产品 | 税/券商行情全包，或未来价格不变；不能把5年档价格当完整历史价 |
| E08 | [Sharadar 基本面字段及维度](https://sharadar.com/docs/fundamentals) | AR/MR 和当前日期字段语义不同，历史需按可得性选值 | 所有修订、历史日内到达时间都已完整可回放 |
| E09 | [Sharadar 证券母表](https://sharadar.com/docs/tickers) | 具有永久标识和存续信息，下载母表是快照 | 当前行业、规模字段可以任意回填历史 |
| E10 | [Sharadar 个人许可](https://sharadar.com/terms) | 条款第2条明确禁止将服务或衍生数据用于“专业、商业、机构或组织目的”，逐项列出的禁止用途包含面向他人的研究/交易/咨询与**“为企业进行技术开发”**；第10条要求终止后30日内删除本机所有Services Data副本（含downloads、bulk files、caches、extracts）及任何能重建Sharadar表的数据集，可能被要求提交删除声明；终止后允许保留不含、且不能重建Services Data的研究产出、回测结果、模型、汇总统计和交易日志，但不授予终止后再访问或重新下载的权利 | 个人订阅自动允许收费分发衍生排名；日后若VITALIS产品化，本许可本身即禁止继续使用同一订阅产出的原始数据支撑该产品技术开发 |
| E11 | [SEC EDGAR 读取接口](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | 有公开 filings/XBRL、bulk 与更新机制 | 官方原始事实等于已整理完毕的研究级 PIT 数据库 |
| E12 | [FRED：ALFRED 接口说明](https://fred.stlouisfed.org/docs/api/fred/alfred.html) | 可处理宏观历史修订/vintage | 任意当前 FRED 序列都可直接用于历史决策 |
| E13 | [IBKR：Unavailable Historical Data](https://ibkrcampus.com/docs/web-api/v1/endpoints/market-data/unavailable-historical-data) | 到期期权和停止交易证券等存在历史供给限制 | 当前可调用券商工具就代表有全历史研究数据 |
| E14 | [Alpha Vantage：API 文档](https://www.alphavantage.co/documentation/) | 有预测及修正接口；公开所列请求参数未展示任意历史 as-of 查询 | 已经满足逐日多年共识快照的严格需求 |
| E15 | [Alpha Vantage：支持与额度](https://www.alphavantage.co/support/) | 常规免费档25次请求/日 | 本账户一定有付费或特殊项目额度 |
| E16 | [ORATS：Options Data API](https://orats.com/data-api) | Delayed 档199美元/月，有历史及 near-EOD 数据 | 基础股票研究必须采购，或 mid/拟合价都能真实成交 |
| E17 | [Sharadar：Upgrade — Pause & Resume（2026-08-07博文）](https://sharadar.com/blog/posts/upgrade-pause-resume) | 2026-08-07起支持订阅暂停1、2或3个月，当期访问权持续到当前计费周期结束，到选定日期自动恢复计费与访问 | 暂停期间原始数据保留是否豁免E10终止后30日删除义务；博文未提及暂停与终止在数据留存上的区别待遇，不能假设暂停可以规避删除条款 |
| E18 | [Pan / Poteshman：The Information in Option Volume for Future Stock Prices，2006](https://academic.oup.com/rfs/article-abstract/19/3/871/1646711) | 买方发起、开新仓的 put/call 成交量比在其历史样本具有预测力 | 普通未标方向日成交量或ORATS日快照能复制其字段与收益；多空价差等于本项目多头净收益 |
| E19 | [Cremers / Weinbaum：Deviations from Put-Call Parity and Stock Return Predictability，2010](https://doi.org/10.1017/S002210901000013X) | 同行权价看涨/看跌IV差的预测力在期权流动性高、股票流动性低时较强，反向组合较弱 | 所有期权成交量/情绪信号在高流动性股票均无效；该子样本可直接等同于P007候选池 |
| E20 | [Johnson / So：The Option to Stock Volume Ratio and Future Returns，2012](https://www.sciencedirect.com/science/article/pii/S0304405X12000797) | 未标方向O/S的低组历史收益高于高组，卖空成本是其解释之一 | 期权活跃越高越健康；低组减高组多空收益等于只做多收益；所有信息只在空头侧 |
| E21 | [Ge / Lin / Pearson：Why Does the Option to Stock Volume Ratio Predict Stock Returns?，2016](https://www.sciencedirect.com/science/article/pii/S0304405X16000167) | 开仓买入call的交易信息较强，未发现合成空头比合成多头更有信息 | 无方向的日总量可识别该交易类别；其结果可直接实现为本项目月频多头alpha |
| E22 | [ORATS：near-EOD 字段](https://orats.com/near-eod-data)及[Time & Sales API](https://orats.com/docs/time-and-sales-api) | 日快照列出期权成交量、OI和IV；逐笔接口自2022年起有推断的aggressorSide | 日快照有开仓买入标记；推断的主动方等于开平仓分类；产品价格和可用性今后不变 |
| E23 | [Li / Wang：Option-Implied Signals and Crash Risk，2026预印本](https://arxiv.org/html/2608.26115) | 作者报告近期21日smirk衰减，IV spread和偏度代理仍有统计信号；部分模型下一月收益样本外R²接近零 | 已独立复现或同行评审；R²接近零等于排序IC为零；已检验P007期权成交量门槛扣成本后相对QQQ收益 |

## R011扩大研究的新增证据

| ID | 来源 | 支持的判断 | 不能据此推导 |
|---|---|---|---|
| E24 | [QLD：2026-05-31年度股东报告](https://www.proshares.com/globalassets/proshares/documents/annual-reports/annual_qld.pdf) | 截至该日十年基金年化35.76%、纳指100年化22.04%，存在可购买杠杆产品在该窗口获得较高总收益的实盘历史 | 未来收益预测；风险调整后alpha；指数回报等于QQQ基金回报；1.2–1.5倍已被验证最优 |
| E25 | [QLD：招募说明书](https://www.proshares.com/globalassets/proshares/prospectuses/qld_summary_prospectus.pdf) | 日目标与长期回报不同；融资与路径影响净收益；列示2022年第二季度−42.26% | 仅以管理费代表全部杠杆成本；长期收益恒为指数两倍 |
| E26 | [OIC：LEAPS Pricing](https://www.optionseducation.org/optionsoverview/leaps-pricing) | 长期期权价值受波动、利率、股息、时间等共同影响 | LEAPS必然比融资/杠杆ETF便宜，或构成独立alpha |
| E27 | [AQR：Size Matters, If You Control Your Junk](https://www.aqr.com/Insights/Research/Working-Paper/Size-Matters-If-You-Control-Your-Junk)及[实施边界说明](https://www.aqr.com/Insights/Perspectives/There-is-No-Size-Effect-Daily-Edition) | 规模需要与质量联合分析，统计发现与实施收益不同 | 小盘天然有效；本项目此前大盘质量结果已经检验该新方向 |
| E28 | [Cohen / Malloy / Pomorski：Decoding Inside Information](https://www.nber.org/system/files/working_papers/w16454/w16454.pdf) | 作者摘要与NBER介绍区分惯常/非惯常内部人交易 | 旧样本异常组合收益等于当前散户多头扣成本收益；本轮已完整审计或复现论文 |
| E29 | [SEC：Forms 3, 4, 5](https://www.sec.gov/file/forms-3-4-5pdf) | Form 4通常两工作日内披露；交易代码与性质需区分 | 可在内部人成交当天假设公众已知；所有买入代码都是同类公开市场买入 |
| E30 | [AVUV：2026-06-30事实表](https://res.avantisinvestors.com/docs/avantis-us-small-cap-value-avuv-etf-fact-sheet.pdf) | 有小盘低估值/较高盈利能力的可买替代方案，费率0.25% | 已证明今后胜过QQQ，或个人税后净收益等于基金表中数字 |
| E31 | [S&P Global：Capital Market Implications of Spinoffs](https://www.spglobal.com/market-intelligence/en/news-insights/research/capital-market-implications-of-spinoffs) | 分拆历史样本有相对行业的正面研究证据 | 今天所有分拆都值得买，或相对行业超额等于相对QQQ超额 |
| E32 | [Coval / Stafford：Asset Fire Sales](https://www.nber.org/papers/w11357) | 基金资金流约束下的被迫交易可能产生价格压力 | 它直接验证分拆策略；散户一定能判断卖压或获得流动性补偿 |
| E33 | [GeoPark：2024年要约原文件](https://www.sec.gov/Archives/edgar/data/1464591/000095010324004046/dp208425_ex-a1a.htm) | NYSE上市公司真实存在不足100股的受益持有人优先条款，具体资格/竞价/取消条件可查 | 当前仍开放；99股无条件保本；可按账户拆分突破受益所有人限制 |
| E34 | [Cboe PUT：2026-08-31事实表](https://cdn.cboe.com/resources/indices/factsheet/CboeGlobalIndices_PUT-Index.pdf) | 2007-01-03起PUT年化7.1%，同期S&P 500总收益11.0%，机械卖put不能默认提高CAGR | 所有卖期权策略均无效；该指数含散户全部成本；本表提供了QQQ同口径比较 |
| E35 | [Martineau：How Does Earnings News Cause Stock Prices to Move?](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607) | 作者摘要报告大盘PEAD自2006年消失、微盘近期衰减，应核查经典结果的当代适用性 | 所有事件信息均无价值；本轮已重做其完整实证 |

滚动PDF以本轮实际打开的报告日期为准；搜索引擎摘要可能指向旧年份，不能将旧摘要数值与新报告期间拼接。上述来源服务于[12机会筛选](12-retail-opportunity-map.md)，未生成新的投资回测结果。

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
