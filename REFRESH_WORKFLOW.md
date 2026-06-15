# 周期性 LS 复盘工作流

> 用于每周 / 每两周 / 触发事件后快速重启分析。
> 全流程 5 分钟。

---

## 三步走

### 步骤 1：刷新数据（30 秒）

```powershell
cd "E:\Download\storage_stooq_downloader\data\raw"
python storage_stock.py
```

这会重新从 yfinance 拉数据，覆盖 `storage_stocks_ohlcv.xlsx`。

如果某只票交易代码变了（比如 SanDisk 改成别的 ticker），编辑 `storage_stock.py` 里的 `tickers` 列表。

---

### 步骤 2：生成状态报告（10 秒）

```powershell
python refresh_status.py
```

输出包含 6 个部分：

1. **近期表现**（1W / 1M / 3M / YTD 收益 + 最新价）
2. **错配信号**（基于新权重的 mispricing 排名，最被低估 → 最超涨）
3. **Pair Z-scores**（10 个可执行 pair 的 z-score + 半衰期 + 1σ 大小）
4. **量能确认质量**（90 天涨幅有多少来自高量日）
5. **近期成交量趋势**（5 日均量 vs 20 日均量）
6. **3M Narrative 热力图**（板块内排序，看 HBM/NAND/HDD 谁领跑）

**复制全部输出到剪贴板**。

---

### 步骤 3：粘贴模板给 Claude

打开 Claude Code 新会话（同目录），把下面的模板填好粘贴：

```
我准备做存储/内存板块 LS 复盘。

## 状态报告（refresh_status.py 输出）
[此处粘贴脚本的完整输出]

## 当前盘后报价（如果与最后交易日 close 有差）
- WDC:     $___
- SNDK:    $___
- MU:      $___
- Samsung: $___   (USD-denominated futures price)
- Hynix:   $___   (USD-denominated futures price)

## 当前 FX
- KRW/USD = 0.000___   (若过去一周变动 >0.5%，特别说明)

## 我当前持仓
- Pair 1: L ___ / S ___，入场 $___ / $___，持仓 ___ 天，当前 PnL ___%
- Pair 2: L ___ / S ___，入场 $___ / $___，持仓 ___ 天，当前 PnL ___%
- （如无开仓则写"暂无"）

## 不可交易的标的
- Kioxia (东交所，无 USD 期货)
- Seagate / STX (你的 broker meme 币冲突)
- 其他: ___

## 请你做这几件事

1. 检查我现有 pair 是否需要调整（hold / trim / exit）
2. 识别新出现的极值 z-score（|z| ≥ 1.8）—— 这是新机会信号
3. 检查板块 narrative 是否有变化（HBM/NAND/HDD 相对表现）
4. 如有新 pair 推荐，给出：z-score + RR + 周末已吃边际 + 触发表
5. 综合判断：整体是合理同涨 / narrative 切换 / 见顶信号 / 其他
```

---

## Claude 应该回复的结构

✓ **持仓评估**：每个开仓 pair 标记 ✅持有 / ⚠️减仓 / ❌平仓
✓ **新机会**：z 极值 pair 排名（按 RR 排序）
✓ **Narrative 判读**：板块整体处于什么阶段（持续涨/见顶/轮动/回调）
✓ **执行清单**：要平的、要开的、要观望的，配对应价位

如果 Claude 回复**没**这 4 项，明确追问。

---

## 何时该立刻复盘（不等周期）

| 触发 | 原因 |
|---|---|
| 任一持仓 PnL > +5% | 触发分批 TP，需要决策平多少 |
| 任一持仓 PnL < −3% | 接近 SL，需要决策止损还是加仓 |
| 任一持仓股单日跳空 ≥ 5% | 公司特定事件，pair 假设可能破 |
| NVIDIA 关于 Rubin/CMX/BlueField-4 官方更新 | 整体 narrative 锚点 |
| TrendForce / DRAMeXchange 月度 NAND/DRAM 价格 | 影响所有内存名字 |
| 任一持仓股财报前 1 天 | 强制平仓，事件驱动 |
| KRW/USD 周内变动 > 2% | 影响 Samsung/Hynix 隐含 FX |
| Samsung HBM4 NVIDIA 认证新闻 | regime-defining event |
| 持仓 ≥ 5 天且 PnL < +2% | 时间检查节点 |

---

## 何时该完全重做 R01-R04 研究（不只是状态刷新）

不是常规复盘，是结构性重启：

1. **过去 30 天内**某只票涨/跌 ≥ 40%
2. 板块出现新的 narrative（比如 Optical/CXL/PIM 等新存储 form factor）
3. 大型并购 / 拆分（如 Solidigm 独立 IPO、Samsung 内存独立等）
4. 你的权重假设变了（比如对 HBM 在 2027 后的地位有新看法）
5. 增加新标的（Pure Storage / VAST / WEKA 上市后纳入）

那种情况下，回去重跑 `research_01_exposure_matrix/analysis.py` 等所有 4 个研究脚本，重新生成所有图表和 CSV。

---

## 数据集维护小贴士

- yfinance 偶尔会改 ticker 代码（如 Korean stocks 加 ".KS" 后缀变了），运行报错时先检查 `storage_stock.py` 的 tickers
- 默认下载 `period="1y"`，每次会覆盖文件；想要更长历史改成 `period="2y"` 或 `"5y"`
- Korean 股票数据是 KRW 计价，Japanese 是 JPY 计价，US 是 USD 计价——所有跨市场比较都需要 FX 折算（脚本默认用 0.000655 KRW/USD baseline，你给 Claude 的 FX 会精确化）
- 周末数据集和当前 broker 报价差异：refresh_status.py 输出的是 Friday close，期货盘后报价让你单独给 Claude

---

## 常见诊断快查

**问题：Claude 给的 pair 建议跟我的执行价位相差很大**
→ 检查：是否提供了当前 USD 报价？refresh_status 输出是 Friday close 价

**问题：z-score 突然变化很大（>1σ）**
→ 检查：是数据更新引入新数据点，还是 ratio 真的剧烈移动了？看 [1] 部分的近期表现

**问题：持仓时间到了 10 天但 PnL 还没到目标**
→ 不要恋战。按 PLAYBOOK 的时间止损，平 70%

**问题：Claude 推荐的新 pair 跟之前完全不同**
→ 正常。z-score 是动态的，且周末/盘后报价会改变。**只关注当前最高 RR 的 pair**，不要回头追"曾经的好 pair"

---

## 相关文件

| 文件 | 用途 |
|---|---|
| `storage_stock.py` | 数据下载（yfinance）|
| `storage_stocks_ohlcv.xlsx` | 数据文件 |
| **`refresh_status.py`** | **本工作流的核心脚本** |
| **`REFRESH_WORKFLOW.md`** | **本文档** |
| `PAIR_TRADE_PLAYBOOK.md` | 单笔 LS pair 的止盈/止损细则 |
| `RESEARCH_INDEX.md` | 4 个深度研究的索引 + 综合配置 |
| `research_01_exposure_matrix/` | AI 暴露 × 估值散点（基本面框架）|
| `research_02_rotation_pairs/` | Pair ratio z-score 历史轨迹 |
| `research_03_fab_concentration/` | SNDK↔Kioxia 共 fab 风险 |
| `research_04_vol_confirmed_returns/` | 量能确认质量分析 |

---

## 一句话总结

**每次只要：刷新数据 → 跑脚本 → 粘贴报告 + 持仓 + 报价给 Claude → 等回复 → 执行清单**。
平时不用动 R01-R04 研究文件夹；它们的图表只在结构性变化（30%+ 单股移动 / 新标的 / 新权重假设）时重做。
