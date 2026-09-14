# 09 集成审查：现金计息、04诊断与Sharadar接入之后的整体复核

日期：2026-09-13。范围：本次会话新增的全部代码（`vitalis/macro.py`、`stats.py`、`sharadar.py`、`quality.py`、`universe.py`、`build_universe.py`、`reconcile.py`）与相关文档（README、AGENTS、`docs/review/*`、`docs/prototype/*`、`config/*.json`）。目的：找冗余、重复、不一致与漂移，重新评估方法论是否仍然成立，标出被本轮测试推翻或过时的假设，以及尚未覆盖的重要领域。按风险从高到低排列，不是按时间顺序。

## 结论先说

工程层面这轮新增代码质量是好的：44→66项测试全部通过，真实数据核验（S&P500重建113/113季度吻合、价格核对50,460交易日仅2处超差、`tickers`行数两种独立取数方式完全一致）都是真正的独立交叉检查，不是自我复述。**但文档层面出现了几处会误导后续决策的实质性漂移**，而且**目前为止投入的所有真实数据工程都还没有推进研究闭环的第二步（冻结规则）**——`engine.py`和`run.py`一行都没有引用任何新模块。这两点合起来是本次复核最需要立刻处理的问题。

---

## 第一档：会误导决策的文档漂移（已在本轮修正，见下方"已修正"）

### 1. `docs/prototype/README.md` 仍写"实际数据采购为0"

这是原型闭环的**入口文档**，`docs/README.md`建议的阅读顺序会带读者到这里。它写于免费样本阶段，此后从未更新，仍然说"当前无需IBKR Gateway"式的旧状态描述，结尾明确写着"实际数据采购为0"。这是假的——本次会话已经用真实API key下载了Sharadar Full History Bundle的全部A档数据。任何人（包括用户本人几周后回来看）读这份文档都会得到"什么都没花钱"的错误印象。

**已修正**：见本文件末尾的修正记录。

### 2. `docs/review/05-data-and-engineering.md`（权威预算文档）仍写"未购买服务"、"本次未下单"

`docs/README.md`自己规定"供应商和环境在05"是权威位置。05第3行"未购买服务、读取券商账户或验证私有API权限"、第24行"本次未下单"，在真实订阅生效后都不再成立。**更严重的是：目前项目文档里没有任何地方记录用户实际选择的订阅档位、计费周期和真实金额**——我在07/08里只记录了官方定价页的各档报价，从未确认用户到底订了哪一档、月付还是年付。这不是我能替用户填的空，需要用户确认后更新05的"硬预算账本"。

**这是留给用户的问题，不是我能单方面修正的漂移**：请确认实际订阅档位（Bundle/Fundamentals+Prices分开/月付或年付）与首次扣费日期，以便05的预算表反映真实支出而不是情景数字。

### 3. `config/data-source-policy.json`的`license_retention`字段暗示自动执行删除

该字段写"personal_use_license_requires_deletion...within_30_days_of_termination"，读起来像是项目在自动执行这条条款。但用户已明确指示"我们私用，所以必须保存"，`vitalis/sharadar.py`的`check_retention()`也已改为纯只读工具、不被任何代码自动调用。`config/data-source-policy.json`没有跟着更新，是本次发现的第二处"代码行为已变、配置文档没变"的漂移。

**已修正**：见文末修正记录。

### 4. `docs/prototype/historical-data-contract.md`第29行说`check_retention()`"执行...终止后30日删除义务"

同一处漂移的第三个落脚点。措辞是"执行义务"（有强制力的动词），与`sharadar.py`模块文档字符串"deletes nothing, and nothing in this module calls it automatically"矛盾。

**已修正**：见文末修正记录。

### 5. `config/prototype-v1.json`的known_limitations混淆了"价格"与"公司行动"两件事

原文"Yahoo historical corporate actions and adjustment factors not reconciled to an independent source"是一句话概括两件事：(a) 收盘价本身的准确性，(b) 拆股/分红等公司行动记录的准确性。`vitalis/reconcile.py`本轮**只核对了(a)**——30只样本50,460个交易日的收盘价，2处超差。**(b)公司行动本身从未系统核对过**：虽然真实`actions.csv`已经下载到本地（30只样本+QQQ全部有），但从未写代码把Yahoo解析出的拆股/分红事件与Sharadar `actions`表的记录逐条比对。继续用一句话盖住这两个已经产生真实差异的问题，本身就是新的不准确。

**已修正**：拆成两条独立、精确的表述，见文末修正记录。

---

## 第二档：高风险但需要判断的发现（未擅自修改，等待决定）

### 6. 全部新真实数据能力都还没有接入研究闭环

`vitalis/quality.py`、`vitalis/universe.py`、`vitalis/reconcile.py`、`vitalis/sharadar.py`——没有一个被`vitalis/engine.py`或`vitalis/run.py`引用（用`grep "^from \.\|^import"`核实过）。04协议的闭环是"版本化数据→冻结规则→账本→对照→决策"；本轮所有工作严格来说都停留在"更好的数据"这一步，规则、账本、对照、决策四步都还是P001原样。这不是坏事——正是08的D01要求的顺序——但值得明确说出来，避免"做了很多真实数据工程"被误读成"策略研究前进了"。两者是两回事。

### 7. 已有的统计结果比工程进度更值得注意：M10的优势区间跨零

这是本轮已经算出来但没有被足够强调的发现：`20260913T183444969568Z-11f74ee0`那次运行里，M10相对QQQ的CAGR差点估计是+2.50pp，但21日区块自助法给出的p05/p50/p95是**-8.43/+2.58/+12.46pp**——90%区间跨越零。这是在**幸存者偏差样本、只有5年、只测了一个参数组合**这种对策略最友好的条件下得到的结果。换句话说：**即使不修正任何已知偏差，动量信号本身能否与噪声区分开都还没有确定的答案**。

这件事的分量应该重新评估：如果连这个最宽松样本下的统计显著性都不稳固，那么本轮投入的大量工程（真实历史股票池、质量因子真实数据管道）主要是让"证据不足"这个结论建立在更干净的数据上，而不是让"有效"这个结论更可信。这不代表工程没有价值——数据基础设施迟早要做——但如果下一步的优先目标是"尽快知道这个策略到底行不行"，那么**在扩大股票池规模之前，先在现有30只样本上把自助法跑满04要求的稳健性检查（不同区块长度、不同参数邻域）**，可能比继续扩展数据覆盖更快得到答案。

### 8. `test_quality.py`的真实数据验证测试没有真正测到排除银行的逻辑

`RealDataProofTests.test_real_art_fundamentals_produce_finite_quality_scores`给所有真实ticker赋予同一个占位SIC代码（3571），只验证分数落在[0,1]区间，**没有验证JPM/BAC/UNH这些真实银行/保险股会被正确排除**。我在会话中另外写过一次性脚本用真实SIC代码验证过这一点（结果正确：三只银行/保险都落入中性0.5），但那次验证从未变成可重复运行的测试，一次代码改动就可能悄悄破坏这个行为而没有任何测试失败。

**建议**：把那次一次性脚本的验证逻辑收进`test_quality.py`，使用真实`security_master()`或`tickers.csv`里的真实SIC代码，而不是占位符。

### 9. 本轮抓到的一个真实bug说明了这类代码最大的风险模式

`monthly_universe()`最初把`for ticker, info in master.items():`里的字典键（`permaticker`，如"124392"）当成了真正的股票代码使用，导致所有月份市值查询全部落空、返回空名单且不报任何异常——直到被一个合成数据的单元测试发现。这个bug本身已经修好，但它是一个值得记住的模式：**这类"变量名指向错误但类型兼容、不抛异常"的错误，是这个项目里最危险的错误类型**，因为它产生的是"看起来合理但完全错误"的结果，而不是崩溃。往后每新增一个基于字典聚合的函数，都应该有至少一个"如果用错键就会失败"的判别性测试，而不是只测试"结果格式对不对"。

---

## 第三档：代码质量与维护性（建议，不紧急）

### 10. `universe.py`内部有5处几乎逐字重复的zip读取样板

`load_sp500_table`、`security_master`、`distinct_trading_days`、`load_marketcap_snapshots`、`load_dollar_volume`都各自写了一遍：
```python
with zipfile.ZipFile(path) as zf:
    with zf.open(zf.namelist()[0]) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
```
`tests/test_reconcile.py`里也独立重复了第6次。应该提取成一个共享的小helper（放在`universe.py`顶部或未来的`bulk_csv.py`），5-6行代码，收益是往后任何一处的编码/字段错误只需要改一个地方。

### 11. `universe.py`已经承担三个不同的职责

S&P500点时点重建、证券主档、市值/流动性资格筛选，三件事目前挤在一个314行的文件里，而项目里其它模块（`macro.py`/`stats.py`/`quality.py`/`reconcile.py`/`sharadar.py`）都只做一件事。现在拆分不紧急，但如果下一步（历史SIC重建、fundamentals/actions大规模拼接）继续加进这个文件，建议先拆分再加，避免变成难以定位改动影响范围的大文件。

### 12. `quality.py`的`EXCLUDED_SIC_RANGES`与`universe.py`的`ELIGIBLE_CATEGORIES`/`ELIGIBLE_EXCHANGES`都是本项目自定范围，两份文档字符串已如实标注"需要复核"，但从未真正复核过

例如`EXCLUDED_SIC_RANGES`用6000–6299整段排除"depository institutions, credit agencies, brokers/dealers"，但broker/dealer（如嘉信理财一类）的资产负债结构和银行未必适合用同一刀切规则处理；这类边界情况目前没有任何测试覆盖，也没有独立信息源核对过SIC分类边界是否准确。风险不高（已被标注为"provisional"），但如果股票池扩大后出现意外的中性分公司，这是第一个该检查的地方。

---

## 第四档：已知且此前已披露的缺口（按用户要求重申，非新发现）

这些不是本轮新发现，是已经写进代码/文档但值得在这次整体重估里再次点名的：

- **04要求的DSR类多重比较修正**：完全没有实现。一旦quality.py/universe.py真正接入产生新的P003结果，这是发布结论前必须补的。
- **rolling 3Y/5Y Sharpe**（04另一项明确要求）：区块自助法不能替代这个，两者回答不同的问题（前者是"这个信号在不同历史时期表现是否稳定"，后者是"这一个点估计有多大抽样噪音"）。
- **历史SIC重建**：`actions.csv`的`sicchangefrom`/`sicchangeto`字段已确认存在且可用（本轮"Step 2"候选之一），但还没有人用它。`quality.py`真实数据验证用的仍是当前快照SIC。
- **`universe.py`资格筛选只有当前交易所/类别**：模块文档字符串已自曝这一点，历史换所/换类没有处理。
- **股息支付日 vs 除息日**：P001从第一轮起就在用除息日入现金而非真实支付日；真实`actions.csv`已下载但从未检查其中是否含支付日信息、检查后是否值得改账本口径。
- **`check_and_record_quota()`没有文件锁**：单用户单进程场景下不是问题，但如果未来有并发脚本同时调用Sharadar适配器，当前的"读JSON、判断、写JSON"三步没有原子性保证，可能漏记请求数、悄悄超过自定的200次/日上限。

---

## 已修正的漂移（本次审查一并处理）

以下四处是纯粹的事实纠正（不涉及需要用户判断的取舍），审查时一并修正：

1. `docs/prototype/README.md`："实际数据采购为0"→更新为反映真实Sharadar订阅与数据下载状态，并链接到08的完整记录。
2. `config/data-source-policy.json`：`license_retention`字段新增用户已选择长期保留数据的说明，不再读起来像自动执行删除。
3. `docs/prototype/historical-data-contract.md`第29行："执行...删除义务"改为准确描述`check_retention()`的只读/未被调用状态。
4. `config/prototype-v1.json`的known_limitations：原来混在一起的"Yahoo公司行动未核对"拆成"收盘价已核对（50,460交易日，2处超差）"与"拆股/分红等公司行动本身仍未核对"两条独立、精确的表述。

第2项（用户实际订阅档位/金额未记录）留给用户确认，未擅自假设。

## 2026-09-13事后更新

用户已确认实际订阅为Full History Bundle月付69美元；05的硬预算账本已更新为真实数字（不再是499美元年付情景），见[08](08-decisions-and-coverage.md)对应条目。

"第四档"里的"历史SIC重建"已完成（`vitalis/sic_history.py`，98.2%自校验），同时修复了"第9条"指出的`test_quality.py`占位SIC测试缺口，改用真实历史SIC并显式断言JPM/BAC被排除。真实结果：对P001现有30只样本，2021-01-04的历史SIC与当前快照相比0处变化——这30只大盘蓝筹本身没有一家改过分类，因此这次修复没有改变任何已发布的P001/质量因子结论，价值要等候选池扩大到更易变的中小市值公司后才体现。"universe.py职责过多"与"5处zip读取重复"两项仍未处理。
