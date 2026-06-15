# 📈 stockHelper · 每日盯盘助手

> 每天美股开盘前跑一次，用**大白话**告诉你：半导体 / 光模块 / 存储板块里**哪只能加仓、持仓到什么价该卖**。再配合 Claude Code 联网做基本面 + 消息面分析。

不是黑箱选股器，而是把「趋势 + 同板块相对估值 + **量价关系** + 你的买入价」算成人话建议的小工具。

---

## ✨ 特点

- **大白话输出**：🟢 可加仓 / 🟡 观望 / 🔴 别追，每条都给理由，不堆术语。
- **量价关系是核心**：价涨量增 / 价涨量缩 / 价跌量增 / 价跌量缩 + OBV 资金流向。便宜 ≠ 能买，量价不对不给绿灯。
- **「涨过头」只在同板块内部比**：半导体不跟光模块比，避免误判。
- **按你的买入价给卖点**：自动算止损价、止盈①、止盈②，结合是否过热提示卖多少。
- **报告自动归档**：每天存一份带日期的报告，历史可回看。
- **配合 Claude Code 深度分析**：`/分析` 一键联网查市场份额 + 今日利空利好。

---

## 🚀 Quick Start

### 1) 克隆并进入项目
```bash
git clone <你的仓库地址> stockHelper
cd stockHelper
```

### 2) 建虚拟环境 + 装依赖
```powershell
# PowerShell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
```bash
# Git Bash（反斜杠在 bash 里会被吃掉，用正斜杠）
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### 3) 第一次运行（会自动生成持仓模板）
```bash
./.venv/Scripts/python.exe daily_check.py
```
首次运行会创建 `my_positions.csv`。用 Excel 打开，把你的真实持仓填进去（这个文件**不会**上传 GitHub）：
```csv
ticker,buy_price,shares
AAOI,172.00,5
DRAM,69.00,13
```

### 4) 以后每天两步走

**第 1 步 · 出技术面报告**
```bash
./.venv/Scripts/python.exe daily_check.py
```
结果打印到屏幕，并存到 `今日报告.txt` + 归档到 `reports/`。

**第 2 步 · 联网深度分析（可选但推荐）**
另开一个**可联网**的 Claude Code 会话，在项目目录里输入：
```
/分析
```
Claude 会按 `分析指南.md` 联网调研每只持仓的市场份额 + 今日利空利好，三面交叉给结论。

---

## 🛠 自定义

| 想改什么 | 改哪里 |
|---|---|
| 盯哪些股票 | `daily_check.py` 顶部 `WATCHLIST`（同板块至少留 3 只）|
| 你的持仓 | 用 Excel 编辑 `my_positions.csv` |
| 止损/止盈力度 | `daily_check.py` 顶部 `STOP_LOSS_PCT` / `TAKE_PROFIT_1/2` |
| Claude 分析风格 | 编辑 `分析指南.md` |

---

## 📁 文件结构

| 文件 | 用途 |
|---|---|
| `daily_check.py` | **主脚本**：下载行情 → 算指标 → 出大白话报告 |
| `分析指南.md` | Claude 联网深度分析的固定说明书 |
| `.claude/commands/分析.md` | 斜杠命令 `/分析` 定义 |
| `使用说明.md` | 详细使用文档 |
| `requirements.txt` | 依赖清单 |
| `my_positions.csv` | 你的持仓（**本地私有，不入库**）|
| `今日报告.txt` / `reports/` | 生成的报告（不入库）|

> 仓库里还保留着早期更专业的存储板块研究脚本（`analyze_storage.py`、`refresh_status.py` 等），平时用不到。

---

## ⚠️ 免责声明

本工具只做**数据辅助参考，不构成投资建议**。所有信号基于历史行情计算，市场有风险，最终决策与盈亏由你自己负责。

---

## 📜 License

MIT
