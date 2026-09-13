# VITALIS

个人美股研究系统的最小闭环原型。目标：20万–40万美元总投资本金，优先争取扣成本后超过QQQ，最大回撤约30%作为研究验收上限，年度数据费用≤1,000美元。实际策略配置比例待确定，IBKR与LEAPS后置。

## 运行

Python 3.9及以上（需系统IANA时区数据库），仅使用标准库，无需安装第三方依赖。本项目实测环境为Python3.14.7。

```sh
python3 -m unittest discover -s tests -v
python3 -m vitalis.run
python3 -m vitalis.run --offline
python3 -m vitalis.sample_audit
python3 -m vitalis.sample_audit --offline
```

首次运行需要联网，下载Yahoo公开日频历史；已有数据缓存后可离线重跑。遇到HTTP错误或缺失交易日会停止并记录失败，不绕过权限、不用虚构行情补缺。

原始响应保存在忽略版本控制的`data/public-yahoo/`；每次运行写入唯一`runs/<run-id>/`。`manifest.json`保存数据与代码哈希、来源和错误；`config.json`在下载前冻结；各场景保存每日净值、交易、持仓、损益贡献、风险旗标和选股决策。`report.md`给出比较，`decision.json`记录下一步，`docs/prototype/experiments.jsonl`追加实验登记。

当前配置在[config/prototype-v1.json](config/prototype-v1.json)：2021–2025历史诊断，30只当前存续股票样本，固定12-1/6-1动量、10/20只等权、行业上限和月度滞回；另比较QQQ、QQQ+现金和简单风险覆盖。预热数据始于2020年。所有本金与成本场景都保留。

## 成绩与限制

[第一轮结果摘要](docs/prototype/p001-results.md)。这是一轮**工程闭环与历史样本诊断**，没有正式投资有效性认证。缺少无幸存者偏差的历史股票池、独立企业行动核对、PIT质量数据、税与真正样本外证据。即使样本收益超过QQQ，正式决策仍为证据不足。

股票成交使用从Yahoo拆股调整OHLC重构的历史名义价、次日开盘与整数股。分红近似在除息日入现金，未采用真实支付日；现金利息为0。QQQ整数股账本与调整收盘总收益代理分别报告，后者为主收益参照。风险旗标留日志但不模拟未知人工处置。公司行动桥接及独立价格/分红/费用PNL核对为内部检查，不能替代供应商审计。

阅读[原型约束](docs/prototype/README.md)、[验证协议](docs/review/04-validation-protocol.md)与[完整文档入口](docs/README.md)。公开数据的使用范围以提供方条款为准，缓存及私有结果不加入版本库。

## 历史数据准备

[P002免费样本验收](docs/prototype/p002-results.md)交叉核对AAPL名义价格、现金分红及一例官方拆股，并验证AR财务截至日过滤。审计命令只使用供应商公开示例，无私有凭证；缓存支持离线重跑。退出0表示检查执行完成，完整历史是否通过另见`audit.json`中的`full_requested_price_history`；执行失败退出2并登记，不能把成功执行当投资认证。

免费样本缺427个请求交易日，只有1只股票财务；当前仍不能做正式历史池质量比较。[历史数据接入清单](docs/prototype/historical-data-contract.md)列明所需文件、时点、费用及P003验收。全量导入、历史股票池和退市结算尚待实现。下一步保持动量规则，先在合格历史池重建基线，再验证质量增量。

用户设置见[数据源接入步骤](docs/prototype/data-source-onboarding.md)，缓存/限流实施约束见[本地数据架构](docs/prototype/local-data-architecture.md)。选定原始文件+Parquet/DuckDB+SQLite目录，当前不要求数据库服务或IBKR Gateway。新[来源政策](config/data-source-policy.json)为设计提案，尚未由现有CLI执行；当前离线重跑使用`--offline`。
