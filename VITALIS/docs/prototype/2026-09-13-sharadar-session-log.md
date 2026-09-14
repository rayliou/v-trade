# 2026-09-13 工作记录与交接检查点

分支：`sharadar-integration-and-04-protocol-metrics`（基于`main` @ `127e546`，**当前6个提交领先main、尚未合并**）。最新提交：`27ad894`。本文件是可扫描索引；每项决定的完整理由、验证结果与证据来源见[08决策记录](../review/08-decisions-and-coverage.md)对应条目（篇幅很长，按日期找对应小节即可），不在此重复推导过程。

## 如果你是接手这个项目的人，从这里开始

1. **先读这三份，再动手**：[CLAUDE.md](../../CLAUDE.md)（架构与不变量）、本文件（当前状态与下一步）、[p003-pit-long-history-results.md](p003-pit-long-history-results.md)（目前唯一真正意义上的"新证据"）。
2. **运行`python3 -m unittest discover -s tests -v`确认90项测试全过**（约110秒，其中约35–70秒花在真实数据流式扫描上，属正常）。
3. **不要在后台任务运行`vitalis/run_pit.py`等长任务时编辑`vitalis/*.py`**——Python已把旧字节码载入内存，traceback会显示编辑后的源码行号却对应旧的执行逻辑，非常容易误诊（本轮debug时真实踩过这个坑）。
4. **当前唯一的真实研究结论**（见下方"核心发现"）：收益优势首次统计显著，但同一规则真实回撤远超30%上限；风险覆盖版本反过来。**没有一个已测配置同时满足用户的两个目标**。下一步应该测试"能否找到两者兼顾的风险控制方式"，不要退回去重新论证"动量是否有效"。
5. **真实Sharadar数据在`data/authorized/sharadar/`（未纳入版本库，2.4GB+）**，API key只在本机`.env`（未纳入版本库）。没有这两样东西，`tests/`里所有`RealData*Tests`/`Real*ProofTests`会自动跳过，不会报错，属正常降级行为。

## 核心发现（P003，2005–2025真实点时点、真实价格长历史）

用`config/prototype-v1.json`完全相同的规则（12-1/6-1动量、10/20只等权、月度调仓、滞回），替换成真实按月候选池+真实Sharadar价格+21年窗口（而非固定30只survivor+Yahoo+5年）：

- M10相对QQQ的CAGR优势**首次统计上不跨零**（90%区间[+0.18,+13.00]pp），但真实最大回撤-58.89%，远超用户30%研究上限。
- 加15%波动目标的风险覆盖版本把回撤压到-32.64%（改善本身统计显著），但收益优势的置信度整个跌回不确定区间（[-5.70,+6.05]pp）。
- **两个目标（跑赢QQQ、回撤≤30%）目前没有一个配置能同时满足**——这是收益与风险的真实取舍，不是"策略无效"或"策略有效"的证据。

完整方法论、预注册声明、真实公司行动（BellSouth 2006年被AT&T收购、Forest Labs 2014年被Actavis收购）验证细节见[p003-pit-long-history-results.md](p003-pit-long-history-results.md)。

## 变更摘要（按主题，本次会话全部内容）

| 主题 | 新增/修改 | 状态 |
|---|---|---|
| 现金计息会计修正 | `vitalis/macro.py` | 完成，已重跑验证 |
| 04验证协议最低输出 | `vitalis/engine.py`（Sortino/Calmar等）、`vitalis/stats.py`（配对区块自助法） | 完成 |
| Sharadar真实订阅接入 | `vitalis/sharadar.py` | 完成，用户已确认69美元/月Full Bundle |
| 质量因子真实数据验证 | `vitalis/quality.py` | 管道验证完成，未接入官方结果 |
| 历史标普500点时点重建 | `vitalis/universe.py`（`load_sp500_table`等） | 完成，113/113季度自校验 |
| 独立价格核对 | `vitalis/reconcile.py` | 完成，30只样本核对 |
| 按月PIT候选池（03第1节规则） | `vitalis/universe.py`（`monthly_universe`等）、`vitalis/build_universe.py` | 完成，79个月每月200只 |
| 历史SIC重建 | `vitalis/sic_history.py` | 完成，98.2%自校验；对现有30只样本无影响 |
| **真实长历史回测（P003）** | `vitalis/sharadar_prices.py`（新）、`vitalis/run_pit.py`（新） | **完成，见上方核心发现** |
| 文档漂移审查与修正 | 09号审查文档、05预算账本更新 | 完成 |
| 全流程并行化 | `run.py`/`run_pit.py`均用`ProcessPoolExecutor` | 完成 |

## 本轮修复的真实bug（供以后类似工作参考模式）

三次"无异常但结果全错"或"未处理真实边界情况"的bug，均由测试或真实数据本身暴露，不是人工审查发现：

1. `monthly_universe()`把字典键（permaticker）误用作股票代码，静默返回空月度名单——合成数据单元测试发现。
2. `sic_history.py`早期版本比较`"5990.0"`（真实actions表格式）与`"5990"`（真实tickers表格式），字符串不等导致0%自校验通过率——真实数据自校验发现。
3. `engine.py`对持仓中止（真实公司被收购/退市）只会抛裸`KeyError`，真实21年800只代码历史中3次真实发生——改为按最后已知价强制结算清仓，非排除式处理（排除即将退市的股票会引入新的前视偏差）。

## 尚未做的事（当前诚实边界）

- 只测了"不控制"与"15%固定波动目标"两种风险处理方式；两者之间或核心+卫星等其他形式均未测试。**这是最值得做的下一步**。
- 04要求的DSR类多重比较修正仍未实现——P003是继P001之后第二个真正独立候选，再加候选前应该补上。
- 质量因子（`quality.py`）仍未与真实候选池/长历史结合验证；历史SIC对现有30只样本恰好没有变化，价值待候选池扩大后体现。
- 交易所/行业分类仍是当前快照，`universe.py`的资格筛选未处理历史换所换类。
- `test_quality.py`已用真实历史SIC测试银行排除逻辑；但quality.py本身尚未在P003的真实候选池上跑过。
- 分支尚未合并到`main`，也未与用户确认是否要合并。

## 许可与凭证（重申，见07的E10/E17）

Sharadar Personal Use License禁止商业用途，终止后30日理论上应删除数据；用户已明确要求**长期保留、不受此约束**，`vitalis/sharadar.py`的`check_retention()`已改为纯只读工具，不被任何代码自动调用。真实API key只存在于本机`.env`（gitignore）。

## 提交记录

`0113896`现金计息+04诊断+Sharadar接入 → `964ffbf`标普500重建+独立价格核对+并行化 → `6c02ae0`按月PIT候选池 → `77caf6c`文档漂移审查修正 → `76fa1e1`历史SIC重建 → `27ad894`P003真实长历史回测（当前HEAD）。
