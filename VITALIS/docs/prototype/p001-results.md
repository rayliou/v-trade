# VITALIS 第一轮研究原型结果

实验：`P001-fixed-momentum-engineering-sample`；运行：`20260913T160725371144Z-21e56c60`。

**决策：正式投资有效性证据不足。工程原型已完成历史样本闭环；不能据此认定策略能持续跑赢QQQ。**

用户目标：总投资本金20万–40万美元，优先扣成本后超过QQQ，最大回撤约30%作为研究上限；数据年费≤1,000美元。
本次区间：2021-01-04至2025-12-31，1255个交易日；股票样本30只。

## 同期结果

下表为20万美元资金、单次买/卖10bps成本场景；股票策略已扣每年600美元假设系统现金费。费用按252交易日年化；未计税、现金利息及机会成本。

| 方案 | 净CAGR | 相对QQQ总收益差 | 最大回撤 | Ulcer | 最长水下交易日 | 平均股票数 | 执行费用USD | 系统费用USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ-total-return-proxy | 15.01% | +0.00pp | -35.12% | 13.55 | 493 | 1.0 | 200 | 0 |
| QQQ | 14.75% | -0.27pp | -34.88% | 13.48 | 517 | 1.0 | 199 | 0 |
| QQQ-cash15 | 12.79% | -2.22pp | -21.47% | 8.68 | 410 | 1.0 | 1,281 | 0 |
| M10 | 17.47% | +2.46pp | -22.77% | 6.49 | 472 | 10.0 | 3,277 | 2,988 |
| M20 | 16.32% | +1.31pp | -27.07% | 8.70 | 385 | 20.0 | 1,057 | 2,988 |
| M10-risk15 | 14.96% | -0.05pp | -19.44% | 6.21 | 397 | 10.0 | 3,513 | 2,988 |

QQQ-total-return-proxy使用调整后收盘比例代表分红再投，仅起始开盘为调整价代理；QQQ整数股账本的分红留在现金中，两者分别展示。QQQ-cash15与M10-risk15采用同一15%波动预算、月度滞后估计，但不是两个组合波动恰好相同的保证。

## 样本目标检查

| 股票方案 | 超过QQQ总收益代理？ | 最大回撤≤30%？ | 两项同时满足？ | 12%单名风险复核天数 |
|---|---|---|---|---:|
| M10 | 是 | 是 | 是 | 26 |
| M20 | 是 | 是 | 是 | 0 |
| M10-risk15 | 否 | 是 | 否 | 26 |

通过仅表示本样本的数值条件，并非满足完整04验证协议、全经济成本门槛或已取得统计证据。降低仓位若让年化落后QQQ，仍未满足当前收益目标。单名12%风险复核只留日志，本版未假设一个人工投资者自动及时处理它。

## 资金与成本敏感性

| 资金USD | 买/卖成本bps | 方案 | 净CAGR | 相对QQQ差 | 回撤 |
|---:|---:|---|---:|---:|---:|
| 200,000 | 5 | M10 | 17.55% | +2.52pp | -22.76% |
| 200,000 | 5 | M20 | 16.36% | +1.33pp | -27.09% |
| 200,000 | 5 | M10-risk15 | 15.11% | +0.08pp | -19.44% |
| 200,000 | 10 | M10 | 17.47% | +2.46pp | -22.77% |
| 200,000 | 10 | M20 | 16.32% | +1.31pp | -27.07% |
| 200,000 | 10 | M10-risk15 | 14.96% | -0.05pp | -19.44% |
| 200,000 | 25 | M10 | 17.02% | +2.04pp | -22.78% |
| 200,000 | 25 | M20 | 16.11% | +1.14pp | -27.12% |
| 200,000 | 25 | M10-risk15 | 14.51% | -0.47pp | -19.48% |
| 400,000 | 5 | M10 | 17.78% | +2.76pp | -22.80% |
| 400,000 | 5 | M20 | 16.49% | +1.46pp | -27.43% |
| 400,000 | 5 | M10-risk15 | 15.31% | +0.28pp | -19.49% |
| 400,000 | 10 | M10 | 17.61% | +2.60pp | -22.80% |
| 400,000 | 10 | M20 | 16.43% | +1.41pp | -27.46% |
| 400,000 | 10 | M10-risk15 | 15.12% | +0.11pp | -19.49% |
| 400,000 | 25 | M10 | 17.22% | +2.24pp | -22.83% |
| 400,000 | 25 | M20 | 16.25% | +1.27pp | -27.41% |
| 400,000 | 25 | M10-risk15 | 14.66% | -0.32pp | -19.53% |

## 证据边界

- Thirty current survivor names, not a point-in-time market-cap universe; historical losers and delistings absent
- Static contemporary sector labels; historical classifications not verified
- Yahoo historical corporate actions and adjustment factors not reconciled to an independent source
- Dividends credited as cash on ex-date, not actual payment date; dividend timing is approximate
- Assumes every Yahoo bar is executable; spread/market impact approximated by fixed bps
- Integer-share benchmark retains dividend cash; adjusted-close QQQ reference separately shows total-return proxy
- No taxes, cash interest, quality factor, theme graph, LEAPS, or IBKR
- No untouched holdout or statistical confidence test; this is a fixed-rule historical diagnostic
- Daily 12-percent single-name hard review is recorded but not automatically executed

## 贡献与规则诊断

| 股票方案 | 最大正贡献证券 | 占正贡献总额比例 |
|---|---|---:|
| M10 | NVDA | 18.4% |
| M20 | NVDA | 18.7% |
| M10-risk15 | NVDA | 19.0% |

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

6项标准库单元测试通过；网络运行与离线重跑的收益/回撤指标一致，交易及持仓CSV逐字节一致；31份源快照、全部产物哈希、所有30个方案场景的每日独立损益和累计贡献核对通过，现金余额均非负。

本地完整产物目录：`runs/20260913T160725371144Z-21e56c60`。详细行情与交易输出忽略版本控制，其他机器按根README重跑。

[来源、代码哈希及完整场景指标](p001-metadata.json)只保存访问/配置元数据和汇总结果；完整原始响应、每日持仓和交易文件留在本地忽略目录。
