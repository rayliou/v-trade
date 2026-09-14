# VITALIS 第一轮研究原型结果

实验：`P001-fixed-momentum-engineering-sample`；运行：`20260913T200806896186Z-def1778d`。

**决策：正式投资有效性证据不足。工程原型已完成历史样本闭环；不能据此认定策略能持续跑赢QQQ。**

用户目标：总投资本金20万–40万美元，优先扣成本后超过QQQ，最大回撤约30%作为研究上限；数据年费≤1,000美元。
本次区间：2021-01-04至2025-12-31，1255个交易日；股票样本30只。

本轮为**文档口径修正重跑**，非新策略尝试，账本与选股结果与上一轮完全一致（summary.json逐字节相同，含固定种子自助法结果）：09号集成审查发现`known_limitations`把"Yahoo价格"与"Yahoo公司行动"混在同一条断言里，而`vitalis/reconcile.py`本轮已经独立核对过前者（50,460交易日仅2处超差），后者仍未核对；已拆成两条精确表述。现金计息修正后的中间版本`20260913T182421393889Z-ae9e7167`（数值不同于本轮，无04诊断）保留在本地`runs/`供比较；上一轮`20260913T183444969568Z-11f74ee0`与本轮数值逐字节相同，仅本轮文档口径更精确，故未重复保留。完整审查见[09](../review/09-2026-09-13-integration-audit.md)。

## 同期结果

下表为20万美元资金、单次买/卖10bps成本场景；股票策略已扣每年600美元假设系统现金费。费用按252交易日年化；未计税及机会成本；未投资现金按FRED三个月期国库券二级市场利率(DGS3MO)计息，作为可获得现金收益的上界代理，不是已核实的券商实际计息条款。

| 方案 | 净CAGR | 相对QQQ总收益差 | 最大回撤 | Ulcer | 最长水下交易日 | 平均股票数 | 执行费用USD | 系统费用USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ-total-return-proxy | 15.01% | +0.00pp | -35.12% | 13.55 | 493 | 1.0 | 200 | 0 |
| QQQ | 14.80% | -0.22pp | -34.87% | 13.46 | 517 | 1.0 | 199 | 0 |
| QQQ-cash15 | 13.67% | -1.35pp | -20.95% | 8.37 | 392 | 1.0 | 1,308 | 0 |
| M10 | 17.51% | +2.50pp | -22.76% | 6.48 | 472 | 10.0 | 3,281 | 2,988 |
| M20 | 16.36% | +1.34pp | -27.05% | 8.69 | 384 | 20.0 | 1,054 | 2,988 |
| M10-risk15 | 15.46% | +0.45pp | -19.43% | 6.05 | 397 | 10.0 | 3,541 | 2,988 |

QQQ-total-return-proxy使用调整后收盘比例代表分红再投，仅起始开盘为调整价代理；QQQ整数股账本的分红留在现金中，两者分别展示。QQQ-cash15与M10-risk15采用同一15%波动预算、月度滞后估计，但不是两个组合波动恰好相同的保证。

## 样本目标检查

| 股票方案 | 超过QQQ总收益代理？ | 最大回撤≤30%？ | 两项同时满足？ | 12%单名风险复核天数 |
|---|---|---|---|---:|
| M10 | 是 | 是 | 是 | 26 |
| M20 | 是 | 是 | 是 | 0 |
| M10-risk15 | 是 | 是 | 是 | 22 |

通过仅表示本样本的数值条件，并非满足完整04验证协议、全经济成本门槛或已取得统计证据。降低仓位若让年化落后QQQ，仍未满足当前收益目标。单名12%风险复核只留日志，本版未假设一个人工投资者自动及时处理它。

## 补充指标（04协议最低输出）

命中率为交易日日收益>0的比例，不是逐笔或逐次调仓口径；Sortino/Calmar分母为零或历史不足一年时留空，不显示无限优秀；下行捕获率用QQQ总收益代理下跌交易日的复利收益作分母，QQQ全程无下跌日时留空。

| 方案 | Sortino(零目标) | Calmar | 最差季度 | 日胜率 | 下行捕获率(对QQQ代理) |
|---|---:|---:|---:|---:|---:|
| QQQ-total-return-proxy | 1.05 | 0.43 | -22.54% | 54.74% | N/A |
| QQQ | 1.05 | 0.42 | -22.38% | 54.82% | 1.00 |
| QQQ-cash15 | 1.28 | 0.65 | -10.41% | 54.90% | 0.99 |
| M10 | 1.42 | 0.77 | -8.86% | 54.82% | 0.98 |
| M20 | 1.47 | 0.60 | -16.54% | 54.10% | 0.98 |
| M10-risk15 | 1.47 | 0.80 | -6.69% | 54.90% | 0.96 |

## 统计不确定性（配对区块自助法）

仅对200,000美元/10bps场景运行，种子20260913、2000次重抽样，区块长度21个交易日为预先登记的主口径，63个交易日为稳健性对照；每次重抽样对策略与QQQ总收益代理使用完全相同的区块顺序，保留两者共同的市场路径。区间描述单一历史路径在固定规则下的重抽样不确定性，不单独构成通过前视偏差、幸存者偏差或多重比较修正的显著性证据；完整`bootstrap.json`见各方案目录。

| 方案 | 区块(日) | CAGR差 p05/p50/p95 (pp) | Sharpe差 p05/p50/p95 |
|---|---:|---|---|
| QQQ-cash15 | 63 | -7.51/-1.55/+4.73 | -0.03/+0.15/+0.35 |
| QQQ-cash15 | 21 | -8.46/-1.29/+4.90 | -0.04/+0.16/+0.36 |
| M10-risk15 | 63 | -10.70/+0.62/+11.79 | -0.17/+0.29/+0.76 |
| M10-risk15 | 21 | -11.38/+0.45/+10.96 | -0.20/+0.28/+0.73 |
| QQQ | 63 | -0.48/-0.22/-0.00 | -0.01/-0.00/+0.00 |
| QQQ | 21 | -0.50/-0.21/+0.03 | -0.01/-0.00/+0.00 |
| M10 | 21 | -8.43/+2.58/+12.46 | -0.17/+0.25/+0.67 |
| M10 | 63 | -8.10/+2.72/+12.87 | -0.17/+0.27/+0.68 |
| M20 | 63 | -6.12/+1.36/+8.10 | +0.01/+0.29/+0.61 |
| M20 | 21 | -6.87/+1.38/+8.83 | -0.02/+0.28/+0.62 |

## 资金与成本敏感性

| 资金USD | 买/卖成本bps | 方案 | 净CAGR | 相对QQQ差 | 回撤 |
|---:|---:|---|---:|---:|---:|
| 200,000 | 5 | M10 | 17.57% | +2.54pp | -22.75% |
| 200,000 | 5 | M20 | 16.40% | +1.38pp | -27.07% |
| 200,000 | 5 | M10-risk15 | 15.64% | +0.62pp | -19.38% |
| 200,000 | 10 | M10 | 17.51% | +2.50pp | -22.76% |
| 200,000 | 10 | M20 | 16.36% | +1.34pp | -27.05% |
| 200,000 | 10 | M10-risk15 | 15.46% | +0.45pp | -19.43% |
| 200,000 | 25 | M10 | 17.05% | +2.07pp | -22.78% |
| 200,000 | 25 | M20 | 16.17% | +1.19pp | -27.10% |
| 200,000 | 25 | M10-risk15 | 15.00% | +0.02pp | -19.45% |
| 400,000 | 5 | M10 | 17.79% | +2.76pp | -22.79% |
| 400,000 | 5 | M20 | 16.51% | +1.48pp | -27.43% |
| 400,000 | 5 | M10-risk15 | 15.78% | +0.75pp | -19.42% |
| 400,000 | 10 | M10 | 17.64% | +2.63pp | -22.80% |
| 400,000 | 10 | M20 | 16.46% | +1.44pp | -27.45% |
| 400,000 | 10 | M10-risk15 | 15.61% | +0.59pp | -19.43% |
| 400,000 | 25 | M10 | 17.25% | +2.27pp | -22.83% |
| 400,000 | 25 | M20 | 16.29% | +1.31pp | -27.40% |
| 400,000 | 25 | M10-risk15 | 15.15% | +0.17pp | -19.48% |

## 证据边界

- Thirty current survivor names, not a point-in-time market-cap universe; historical losers and delistings absent
- Static contemporary sector labels; historical classifications not verified
- Yahoo unadjusted closing prices independently cross-checked against real Sharadar stocks data for these 30 symbols: 50,460 compared sessions, 2 discrepancies over 0.05% relative tolerance (one, XOM 2020-02-07, unexplained by any known corporate action)
- Yahoo-derived split/dividend corporate-action events themselves (as distinct from closing prices) have not been reconciled against Sharadar's real actions table, despite that data now being available locally for these symbols
- Dividends credited as cash on ex-date, not actual payment date; dividend timing is approximate
- Assumes every Yahoo bar is executable; spread/market impact approximated by fixed bps
- Integer-share benchmark retains dividend cash; adjusted-close QQQ reference separately shows total-return proxy
- No taxes, quality factor, theme graph, LEAPS, or IBKR
- Cash yield uses FRED's 3-month Treasury bill secondary-market rate (DGS3MO), forward-filled over bond-market holidays, as an upper-bound proxy for obtainable short-duration cash yield; actual brokerage sweep crediting, minimum-balance thresholds, and any account-level haircut are unverified
- No untouched holdout or statistical confidence test; this is a fixed-rule historical diagnostic
- Daily 12-percent single-name hard review is recorded but not automatically executed

## 贡献与规则诊断

| 股票方案 | 最大正贡献证券 | 占正贡献总额比例 |
|---|---|---:|
| M10 | NVDA | 18.4% |
| M20 | NVDA | 18.6% |
| M10-risk15 | NVDA | 19.1% |

比例以正贡献总额为分母，负贡献另保留，不能把赢家占比等同于独立押注数。每个方案`contributions.csv`的价格损益+分红−执行费，再减固定费，独立核对到期末财富。
20只版保留门槛为排名≤40，但样本只有30只；只要仍符合资格和行业约束，原有20只很少因排名退出。因此M20更接近初始选中的存续股票篮子，不代表200只历史股票池中的动态20只策略。
内部公司行动桥接检查：0项超过0.2pp的价格/分红/拆股与调整收益差异。这仅检查同源内部一致性，不替代独立来源核对。

本次实际购买数据费用为0。600美元是运行费用情景；它不是实际账单，也不包含开发维护时间。30%的研究上限不能保证未来损失不会超限。

## 闭环与下一轮

数据源、查询时间范围与响应哈希在`manifest.json`；规则在`config.json`；日净值、持仓、交易与风险旗标分别写CSV，选股分数与信号/成交日期在各方案`decisions.json`。所有30个资金/成本/方案组合均保留，不只展示胜者。

1. 先检查PIT证券母表和公司行动样本的数据可得性与预算，再替换当前存续股票样本；不能继续在本样本上挑参数证明alpha。
2. 可靠PIT基本面合格后，增加质量对照；当前动量结果不为质量或LEAPS背书。
3. 账户税制与真正策略资金比例确认后重算净价值；IBKR仍后置。
4. 新实验先冻结变更与验证区间，再运行并登记继续/修改/停止/证据不足。

`decision.json`登记本轮结论，项目实验日志在`docs/prototype/experiments.jsonl`。

## 核查结果

66项标准库单元测试通过（含独立价格核对、真实标普500历史成分股自校验、真实按月候选股票池构建等模块）；本轮重跑与上一轮`summary.json`逐字节相同，确认改动仅为文档口径（known_limitations拆分），未触及任何账本或选股逻辑；32份源快照、全部产物哈希、所有36个方案场景的每日独立损益和累计贡献核对通过，现金余额均非负。

本地完整产物目录：`runs/20260913T200806896186Z-def1778d`。详细行情与交易输出忽略版本控制，其他机器按根README重跑。

[来源、代码哈希及完整场景指标](p001-metadata.json)只保存访问/配置元数据和汇总结果；完整原始响应、每日持仓和交易文件、各方案`bootstrap.json`留在本地忽略目录。
