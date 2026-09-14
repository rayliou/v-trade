# P004工程审计：已修复与未验收分开

## 已修复

| 问题 | 证据/影响 | 修复/验证 |
| --- | --- | --- |
| 同月月末输入用于月初交易 | 旧252个评估月全部存在候选差异，平均约6只未来新增候选 | 映射到下月，未来输入改变不能改变本月执行；缺月失败 |
| 名义价格×拆股调整成交量 | 本地SEP数据字典明确close/volume均拆股调整 | 成交额用源close×volume；4:1拆股单位回归 |
| 无开盘报价目标直接索引 | 第一次修正run在2014-07-01失败 | 记录未成交、留现金、不替补，保留失败run |
| 质量扩大同业组只比较回退成员 | 旧41,957个计算证券月中2,849个实际同业少于10只 | 完整上级组成员与按组分位；同行回归及peer_count |
| P003缺代码/源哈希与实验登记 | 旧manifest只有配置哈希 | 实际SHA-256核验、代码复制、输出哈希、SQLite快照/文件目录、成功失败登记 |
| 研究入口可在线补缺 | P003曾自动初始化QQQ/FRED | P004精确缓存只读；缺缓存不打开网络；运行remote_requests=0 |
| 通用输入被误认自身侧录 | 非zip JSON数组/压缩/脚本无法通用登记 | 仅zip匹配provenance，补三类回归 |

## 当前数据门槛

| 门槛 | 通过 |
| --- | --- |
| month_end_timing | True |
| source_checksums | True |
| price_completeness | True |
| corporate_action_bridge | False |
| economic_exit_settlement | False |
| execution_quote_coverage | False |
| historical_security_metadata | False |

价格完整与账本恒等式通过不等于经济行动处理通过；当前门槛总结果为False。内部桥接只是现金持有模型与调整价格的一致性检查，不是独立源认证。

- 总桥接差异1071条，评估期内753条，直接持仓日期5条。
- 未验证最后价退出64条方案事件，涉及23只证券；无报价目标未成交11条。方案事件不是独立公司事件。
- 全历史566,335个拆股/分红键无重复，重复记录不能解释本轮差异。

| 分类 | 条数 |
| --- | --- |
| spinoff_context_unresolved | 160 |
| outside_evaluation | 318 |
| no_matching_action_unresolved | 580 |
| split_context_unresolved | 8 |
| dividend_context_unresolved | 5 |

附近±3日行动仅作分类；未持仓异常也可能影响复权信号，不能自动忽略。source中仍有IPO/发行人ID、当前主档、已更正AR历史交付时点及行业链覆盖等边界。

## 直接持仓分拆异常

| 证券 | 日期 | 现金模型-调整收益差(pp) | 方案 |
| --- | --- | --- | --- |
| VLO | 2013-05-02 | -8.65 | M10, M10-risk15, M20 |
| VZ | 2006-11-20 | -3.61 | Q20 |
| TFCF | 2013-07-01 | -11.71 | M20 |
| MRO | 2011-07-01 | -39.29 | M10, M10-risk15, M20 |
| WMB | 2012-01-03 | -18.04 | Q20 |

现有ACTIONTYPES字典将spinoff定义为每股母公司分配的子公司股数，将spinoffdividend定义为分配股票的美元价值。后者不是现金支付，不能直接假设立即变现。此前引擎只接收split/dividend，遗漏分拆权益；必须接入子公司持股与后续交易/处置账本。

## 质量与缓存

质量覆盖51,800证券月，N/A 9,843（19.0%）。N/A包含有意排除的金融/REIT、无申报和缺指标；中性0.5不是质量合格。修复后实际计算同业最小10只。

缓存raw zip不变，派生日历/市值/价格gzip JSON按源哈希、规范化代码及范围命中并校验，禁止pickle。SQLite仅snapshot/artifact目录；共享采集限流、分页重试、并发发布租约、coverage目录及Parquet/DuckDB查询层尚未实现。本轮没有远程采集，不消耗源并发/时间额度。

## 重跑与验证

```sh
python3 -m vitalis.run_pit --offline --max-workers 4
python3 -m scripts.cash_yield_sensitivity --source-run runs/20260913T230115679698Z-pit-170d681b
python3 -m scripts.build_p004_report --source-run runs/20260913T230115679698Z-pit-170d681b --cash-run runs/20260913T230622689020Z-cash0-325597b5
python3 -m unittest discover -s tests -v
git diff --check
```

执行前后源文件哈希核对，每个run唯一且保留代码/配置。报告生成检查其输入产物哈希；Notebook核对源和输出哈希。最终完整103项测试通过（177.880秒）；质量/通用登记修正也通过35项相关回归。Notebook的5个代码单元已执行，源/输出哈希与时点断言通过。

完整异常：主run的data_audit.json；解释序列：diagnostics.json；质量peer_count：quality_details.json；真实费用场景：cost_scenarios.json。
