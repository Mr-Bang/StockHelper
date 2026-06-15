# 存储/内存板块 — 综合研究索引与投资分配建议

> 基于 2026 AI 推理框架（NAND for KV cache offload + HBM 仍核心 + HDD 短缺）下的 7 只存储/内存股横向研究
>
> 数据：1 年日频 OHLCV（`storage_stocks_ohlcv.xlsx`，2025-06-12 → 2026-06-12）
> 标的：Micron / SanDisk / WDC / Seagate / Samsung / SK Hynix / Kioxia

---

## 研究目录

| # | 研究主题 | 核心问题 | 文件夹 |
|:-:|---|---|---|
| 01 | **AI 结构性暴露矩阵** | 谁的当前估值与基本面暴露最匹配？ | `research_01_exposure_matrix/` |
| 02 | **轮动配对** | HBM→NAND 的 rotation 是否已被定价透支？ | `research_02_rotation_pairs/` |
| 03 | **共 fab 集中度风险** | SNDK+Kioxia 同时持有=真的两个押注吗？ | `research_03_fab_concentration/` |
| 04 | **量能确认收益分解** | 涨幅里有多少是真正"有量参与"的？ | `research_04_vol_confirmed_returns/` |

每个文件夹包含 `analysis.py`（代码）、`README.md`（结论+推荐）、`*.png`（图）、`*.csv`（数据）。

---

## 四个研究的关键发现汇总

### R01 — 暴露 × 估值
- **错配排序**（正=超涨；负=低估）：Kioxia **+26**（最危险）；SanDisk +9；Samsung 集团 +4；Micron −5；Seagate −8；WD −12；**SK Hynix −20**（最被低估）
- Samsung 在**集团口径下被非内存业务（69%）严重稀释**；内存段独立看会是 −22 严重低估

### R02 — 短期相对动量
- **SK Hynix / Micron z = −1.70**（最强 mean-rev 信号）：Micron 60 天内透支了 rotation 走势，**短期反转有利 Hynix**
- 全部 4 个 pair 同向指出：Micron 与 SNDK 是过去 60 天的相对赢家
- Samsung 在所有 pair 里都站在"相对便宜"一侧

### R03 — 隐藏集中度
- 实证 SNDK ↔ Kioxia 相关性 = **0.035**（看似最佳 diversifier）
- 这是**时区造假**：SNDK NASDAQ 美东 vs Kioxia TYO 亚洲——日收益几乎不重叠
- 共 fab 事件压力下相关性升至 0.7，diversification benefit 从 28% 跌至 8%
- **SNDK + Kioxia 同时持仓 ≈ 1.2 个押注**，不是 2 个

### R04 — 量能确认质量
- **全板块都是缩量涨**——7 只 quality % 均 ≤30%
- **Kioxia quality = −13%**（高量日竟然亏钱）——病情最重
- Seagate quality = 29%（最健康）
- 你最初对"SNDK 缩量上涨"的怀疑**部分成立但范围更广**：全板块都缩量，Kioxia 远比 SNDK 更虚

---

## 综合矩阵：四个研究的逐股交叉

| 公司 | R01 暴露 | R02 动量 | R03 fab | R04 量能 | **综合** |
|---|:-:|:-:|:-:|:-:|:-:|
| **SK Hynix** | ⬆⬆ 最低估 | ⬆ mean rev 利好 | n/a | ⬇ 量能弱 | **⬆⬆ 超配** |
| **Samsung** | ⬆⬆ 集团稀释 | ⬆ 相对便宜 | n/a | ⬇ 量能弱 | **⬆ 超配** |
| Seagate | ⬆ 略低估 | n/a | n/a | ⬆⬆ 量能最强 | **⬆ 偏多** |
| Micron | ➖ 公允 | ⬇ mean rev 利空 | n/a | ➖ 中性 | **➖ 标配** |
| SanDisk | ⬇ 略超涨 | ⬆ vs Kioxia | ⚠️ 与 Kioxia 共 fab | ⬆ 量能尚可 | **➖ 标配** |
| WD | ⬆ 略低估 | n/a | n/a | ⬇ 量能弱 | **➖ 标配偏少** |
| **Kioxia** | ⬇⬇ 最超涨 | ⬇ 相对偏强 | ⚠️ 与 SNDK 共 fab | ⬇⬇ 高量日亏钱 | **⬇⬇ 强低配** |

---

## 最终建议配置（存储板块内 100%）

### 主推：基于综合矩阵的"结构性偏多 + 短期质量"组合

| 公司 | 权重 | vs 等权偏离 | 角色 |
|---|---:|---:|---|
| **SK Hynix** | **22%** | +8pp | 核心 OW：最低估 + 短期 mean-rev 利好 |
| **Samsung** | **20%** | +6pp | 隐藏的内存段领头羊，被集团稀释 |
| Seagate | 14% | ≈0pp | 量能最干净；HDD 真短缺 |
| Micron | 14% | ≈0pp | 结构好但短期透支；不需主动 OW |
| SanDisk | 13% | −1pp | 结构故事真实，但与 Kioxia 二选一 |
| WD | 10% | −4pp | HDD 故事真实，但量能很弱 |
| **Kioxia** | **7%** | −7pp | 强 UW：4 个研究里 3 个亮红灯 |
| **合计** | **100%** | | |

### 与等权（14.3% 每只）相比，本配置的偏多方向：
- **超配亚洲内存巨头 + Seagate**
- **低配 Kioxia + WD**
- Micron / SNDK 保持中性（结构看好但短期不追）

### Pair-trade 思路（如做相对组合，不是单边持有）

| Pair | 信号强度 | 建议 |
|---|:-:|---|
| LONG Hynix / SHORT Micron | ⭐⭐⭐（z=−1.70） | 最强统计信号；4-8 周窗口 |
| LONG Samsung / SHORT Kioxia | ⭐⭐⭐ | R01+R04 一致：低估 vs 最虚 |
| LONG Seagate / SHORT WD | ⭐⭐ | HDD 内部差异，量能区分明显 |
| LONG SanDisk / SHORT Kioxia | ⭐⭐ | NAND 内部分化；z=+1.08 |

---

## "市场是否在变脆弱"的最终回答

**结构层面**：不脆弱。2026 AI 推理框架（KV cache offload → NAND）是真实的结构性需求转折，企业级 SSD +60% 涨价、Micron NAND +169% YoY、SNDK 数据中心 +233% QoQ 都是硬数据。

**节奏层面**：是的，**领涨结构在变脆**。
1. **量能：全板块缩量涨**，Quality % 均 ≤30%，Kioxia 甚至为负
2. **rotation 透支**：Micron 60 天内跑赢 Hynix 已到 −1.7σ
3. **隐藏集中度**：SNDK + Kioxia 实证相关 0.035，但操作上共用 Yokkaichi
4. **HBM 龙头边际定价权见顶**：Hynix 涨幅温和而绝对估值依然低估，但 marginal flow 已转向 NAND-leveraged 名字

**触发风险（任一即可换领头羊，但不破坏 board 大趋势）**：
- NVIDIA BlueField-4 / Rubin H2 2026 时间表延期
- 三星 HBM4 NVIDIA 认证突破（重大利好 Samsung，相对压制 Hynix）
- Yokkaichi 操作事件（同时打 SNDK + Kioxia）
- NAND 厂商扩产时间表前移，破坏 2027-2028 紧张叙事

**底色判断**：板块整体仍向上，但**最容易被换掉的领头羊是 Kioxia**（4 个维度有 3 个亮红灯）。建议 **从 Kioxia 转仓 → SK Hynix + Samsung**，是当下最高信噪比的调整。

---

## 方法局限

1. 仅 1 年数据；SNDK 和 Kioxia 分别 2025-02 / 2024-12 起上市，**早期数据反映 IPO/拆分独特动力学**
2. 收入构成 % 是公开报告的估计值，非财报实证（实际可能 ±5pp）
3. AI 暴露权重是主观赋值（HBM=1.0, NAND-Ent=1.0...）；不同假设会改变排序
4. z-score mean-rev 半衰期 4-8 周；超出此窗口的判断需别的工具
5. 没有 catalyst calendar、没有 hyperscaler capex 数据、没有 NAND/DRAM 合约价时序——这些都是 augment 当前判断的下一步
6. 未做汇率调整（韩元 / 日元波动对 Samsung / Hynix / Kioxia 名义美元化收益有 ~5-10% 影响）

---

## 接下来可继续做

1. **三星 HBM4 认证情景分析**：如果 Samsung 拿下 HBM4，Hynix 相对承压程度
2. **NAND/DRAM 现货价 vs 个股 beta**：把宏观价格变量纳入定价模型
3. **G3.5 ethernet flash tier 与 BlueField-4 时间敏感性**：每延期 3 个月，SNDK/Kioxia 估值下修幅度
4. **加入未观察 stock**：Solidigm 母公司 SK 海力士 vs 直接 Solidigm 数据；Pure Storage / VAST / WEKA 作为存储栈上游受益者
