# -*- coding: utf-8 -*-
r"""
daily_check.py —— 每天开盘前跑一次的盯盘助手（大白话版）

用法（在项目文件夹里）：
    Windows:  .\.venv\Scripts\python.exe daily_check.py

它会做三件事：
  1. 联网下载你关注的美股最近一年行情（自动覆盖更新）。
  2. 读取你的持仓文件 my_positions.csv（第一次跑会自动建一个模板）。
  3. 打印一份大白话报告：
       - 你的持仓：现在该「继续拿 / 卖一部分 / 全卖 / 止损」，以及具体到什么价。
       - 观察名单：每只票现在「能不能加仓」，并按同板块内部的相对贵/便宜排序。

重要原则：「涨过头」只在【同一个板块内部】互相比。
  比如光模块这几只里谁涨得最猛才算涨过头；半导体不会拿来和光模块比。

你能自己改的地方：
  - 想盯哪些股票 → 改下面 WATCHLIST 里的代码。
  - 你的持仓 → 直接用 Excel 打开 my_positions.csv 编辑（代码、买入价、股数）。
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import yfinance as yf

# Windows 控制台默认 GBK，遇到 emoji/中文会报错；强制用 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPORT_FILE = "今日报告.txt"   # 最新报告（每次覆盖），可用记事本打开
REPORTS_DIR = "reports"        # 历史报告归档目录（按数据日期，全部保留）

# ============================================================================
# 1) 配置区：想盯哪些股票，就在这里加/删代码（都用美股代码）
# ============================================================================
WATCHLIST = {
    "AI半导体":      ["NVDA", "AMD", "AVGO", "TSM", "MRVL"],
    "光模块/光通信":  ["COHR", "LITE", "AAOI", "CIEN"],
    "存储/内存":      ["MU", "SNDK", "WDC", "STX", "DRAM"],
}

# 中文名字（只是为了报告好看；不影响计算）
NAMES = {
    "NVDA": "英伟达", "AMD": "AMD", "AVGO": "博通", "TSM": "台积电", "MRVL": "Marvell",
    "COHR": "相干Coherent", "LITE": "Lumentum", "AAOI": "应用光电", "CIEN": "Ciena",
    "MU": "美光", "SNDK": "闪迪", "WDC": "西部数据", "STX": "希捷",
    "DRAM": "内存ETF(Roundhill)",
}

# 卖出/止损的固定档位（按你的买入价算）。想更激进/保守就改这几个数：
STOP_LOSS_PCT = -0.08   # 跌破买入价 8% 就止损（保护本金）
TAKE_PROFIT_1 = 0.15    # 赚 15% → 卖掉 1/3 锁利
TAKE_PROFIT_2 = 0.30    # 赚 30% → 再卖一部分

POSITIONS_FILE = "my_positions.csv"
CACHE_FILE = "prices_cache.csv"   # 下载失败时用上次的数据兜底


# ============================================================================
# 2) 下载行情（逐只顺序下载，避免 yfinance 多线程的 "database is locked"）
# ============================================================================
def download_all(tickers, period="1y"):
    frames = {}
    failed = []
    print("正在下载行情（逐只）...")
    for t in tickers:
        df = _download_one(t, period)
        if df is None:
            failed.append(t)
        else:
            frames[t] = df
        time.sleep(0.4)  # 轻微间隔，进一步降低被限速/锁库概率
    if failed:
        print(f"  ⚠️ 这几只下载失败，本次跳过：{', '.join(failed)}")
    return frames


def _download_one(ticker, period):
    for attempt in range(3):
        try:
            df = yf.download(ticker, period=period, interval="1d",
                             auto_adjust=True, progress=False, threads=False)
            if df is None or len(df) == 0:
                raise ValueError("返回为空")
            # 单只票有时也会返回多层列名，统一压平成单层
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
            if len(df) < 30:
                raise ValueError(f"数据太少({len(df)}天，新股/新ETF可能如此)")
            return df
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    print(f"  ⚠️ {ticker} 下载失败：{last_err}")
    return None


def build_panels(frames):
    """把每只票的数据拼成几张对齐的宽表：收盘、量、高、低。"""
    close = pd.DataFrame({t: f["Close"] for t, f in frames.items()})
    vol = pd.DataFrame({t: f["Volume"] for t, f in frames.items()})
    high = pd.DataFrame({t: f["High"] for t, f in frames.items()})
    low = pd.DataFrame({t: f["Low"] for t, f in frames.items()})
    close = close.sort_index().ffill()
    vol = vol.reindex(close.index)
    high = high.reindex(close.index)
    low = low.reindex(close.index)
    return close, vol, high, low


def save_cache(close, vol, high, low):
    long = []
    for name, df in [("Close", close), ("Volume", vol), ("High", high), ("Low", low)]:
        m = df.copy()
        m.index.name = "Date"
        s = m.stack().rename(name)
        long.append(s)
    out = pd.concat(long, axis=1).reset_index()
    out.columns = ["Date", "Ticker", "Close", "Volume", "High", "Low"]
    out.to_csv(CACHE_FILE, index=False)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    df = pd.read_csv(CACHE_FILE, parse_dates=["Date"])
    piv = lambda col: df.pivot(index="Date", columns="Ticker", values=col).sort_index()
    return piv("Close"), piv("Volume"), piv("High"), piv("Low")


# ============================================================================
# 3) 指标计算（都封装成函数；报告里再翻译成大白话）
# ============================================================================
def rsi(series, n=14):
    d = series.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def pct(series, days):
    """最近 days 个交易日的涨跌幅（%）。"""
    if len(series) <= days:
        return np.nan
    return (series.iloc[-1] / series.iloc[-1 - days] - 1) * 100


def volume_quality(ret_series, vol_series, win=20):
    """上涨日的平均成交量 / 下跌日的平均成交量。>1 说明涨得有量、健康。"""
    r = ret_series.iloc[-win:]
    v = vol_series.iloc[-win:]
    up_v = v[r > 0].mean()
    dn_v = v[r < 0].mean()
    if not dn_v or np.isnan(dn_v) or np.isnan(up_v):
        return np.nan
    return up_v / dn_v


def obv(close, vol):
    """OBV：能量潮。涨日把成交量加上、跌日减掉，累计起来看资金是在流入还是流出。"""
    sign = np.sign(close.diff().fillna(0))
    return (sign * vol.fillna(0)).cumsum()


def vp_analysis(c, v):
    """
    量价关系分析（核心维度）。返回一个 dict，包含：
      state   : 四象限之一  价涨量增 / 价涨量缩 / 价跌量增 / 价跌量缩 / 量价平稳
      score   : 量价健康分（正=健康，负=警惕），后面直接influence加仓/卖出判断
      desc    : 大白话解释
      obv_div : 是否出现「价升量背离」(价格涨但资金在流出，见顶警号)
      vol5_20 : 近5日均量 / 近20日均量 （>1 放量，<1 缩量）
      quality : 近60日涨幅里有多少来自“放量日”（>50% 说明涨势有真金白银）
      updn    : 上涨日量 / 下跌日量
    """
    c = c.dropna()
    v = v.reindex(c.index)
    n = len(c)
    ret = c.pct_change()

    # --- 近两周价格方向 + 近期放量/缩量 ---
    win = 10
    price_chg = (c.iloc[-1] / c.iloc[-1 - win] - 1) * 100 if n > win else 0.0
    v5 = v.iloc[-5:].mean()
    v20 = v.iloc[-20:].mean()
    vol5_20 = (v5 / v20) if v20 else np.nan

    expanding = (not np.isnan(vol5_20)) and vol5_20 > 1.05    # 近期在放量
    contracting = (not np.isnan(vol5_20)) and vol5_20 < 0.95  # 近期在缩量
    up = price_chg > 2
    down = price_chg < -2

    if up and expanding:
        state, score, desc = "价涨量增", 2, "放量上涨——有资金真金白银在买，最健康，回调可加"
    elif up and contracting:
        state, score, desc = "价涨量缩", -2, "缩量上涨——涨得没量配合，多是虚涨/接近见顶，别追"
    elif down and expanding:
        state, score, desc = "价跌量增", -2, "放量下跌——抛压重，别接刀，持仓要警惕"
    elif down and contracting:
        state, score, desc = "价跌量缩", 1, "缩量回调——抛压在衰竭，趋势没坏的话是健康洗盘，回调到位"
    else:
        state, score, desc = "量价平稳", 0, "近期量价没明显异动"

    # --- OBV 顶背离：近20日价涨，但资金净流出 ---
    o = obv(c, v)
    obv_div = False
    if n > 21:
        price_up_20 = c.iloc[-1] > c.iloc[-21]
        obv_chg_20 = o.iloc[-1] - o.iloc[-21]
        obv_div = bool(price_up_20 and obv_chg_20 < 0)
    if obv_div:
        score -= 1

    # --- 量能质量：近60日涨幅有多少来自放量日 ---
    lr = np.log(c / c.shift(1)).iloc[-60:].dropna()
    vv = v.reindex(lr.index)
    high = vv > vv.rolling(20).mean()
    total = lr.sum()
    # 这个“涨幅有多少来自放量日”只在近60日明显净涨(>~5%)时才稳定；否则分母太小会算出乱码
    quality = (lr[high].sum() / total * 100) if total > 0.05 else np.nan

    return {
        "state": state, "score": score, "desc": desc, "obv_div": obv_div,
        "vol5_20": vol5_20, "quality": quality,
        "updn": volume_quality(ret.dropna(), v.reindex(ret.index).dropna()),
    }


def compute_metrics(close, vol):
    """对每只票算一组原始指标，存进一个 dict。"""
    out = {}
    ret = close.pct_change()
    for t in close.columns:
        c = close[t].dropna()
        if len(c) < 30:        # 至少30天才算；新上市的ETF/股票历史短，部分长周期指标会显示 n/a
            continue
        ma20 = c.rolling(20).mean().iloc[-1]
        ma50 = c.rolling(50).mean().iloc[-1] if len(c) >= 50 else np.nan
        ma200 = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else np.nan
        last = c.iloc[-1]
        out[t] = {
            "last": last,
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "ext50": (last / ma50 - 1) * 100 if ma50 else np.nan,   # 比50日线高/低多少%
            "rsi": rsi(c).iloc[-1],
            "r1w": pct(c, 5),
            "r1m": pct(c, 21),
            "r3m": pct(c, 63),
            "vp": vp_analysis(c, vol[t]),   # 量价关系（核心维度）
        }
    return out


def sector_heat(metrics):
    """
    核心：在【每个板块内部】把成员横向对比，算出每只票的「相对热度」。
    热度 = 板块内 (距50日线乖离 的 z分) 和 (近3月涨幅 的 z分) 的平均。
      热度高 = 在本板块里相对涨过头（别追/考虑减）。
      热度低 = 在本板块里相对落后、便宜（趋势没坏的话是加仓候选）。
    只和同板块比，不跨板块。
    """
    heat = {}
    for sector, tickers in WATCHLIST.items():
        members = [t for t in tickers if t in metrics]
        if len(members) < 3:
            # 同板块不足3只，没法做有意义的横向比，热度记为0（中性）
            for t in members:
                heat[t] = 0.0
            continue
        ext = np.array([metrics[t]["ext50"] for t in members], dtype=float)
        mom = np.array([metrics[t]["r3m"] for t in members], dtype=float)
        z_ext = _zscore(ext)
        z_mom = _zscore(mom)
        composite = np.nanmean(np.vstack([z_ext, z_mom]), axis=0)
        for t, h in zip(members, composite):
            heat[t] = float(h) if not np.isnan(h) else 0.0
    return heat


def _zscore(arr):
    arr = np.asarray(arr, dtype=float)
    mu = np.nanmean(arr)
    sd = np.nanstd(arr)
    if not sd or np.isnan(sd):
        return np.zeros_like(arr)
    return (arr - mu) / sd


# ============================================================================
# 4) 把数字翻译成大白话的「建议」
# ============================================================================
def trend_label(m):
    last, ma50, ma200 = m["last"], m["ma50"], m["ma200"]
    if np.isnan(ma200):
        return ("中性", "数据不足一年，趋势看不全")
    if last > ma50 > ma200:
        return ("上升趋势", "价在50日线和200日线之上，趋势健康")
    if last > ma200:
        return ("中性偏多", "还在200日线上方，但短期走平/回调")
    return ("走弱", "已跌破200日线，趋势转弱")


def add_advice(m, heat):
    """该不该加仓。综合 趋势 + 同板块相对热度 + 量价关系 + 超买。
    返回 (信号灯, 一句话, [理由列表])。"""
    last, ma50, ma200, rsi_v = m["last"], m["ma50"], m["ma200"], m["rsi"]
    vp = m["vp"]
    reasons = []

    # 趋势
    tlabel, tdesc = trend_label(m)
    reasons.append(tdesc)

    # 同板块相对热度
    if heat >= 1.0:
        reasons.append("⚠️ 本板块里相对涨过头（同行中涨最猛的一档）")
    elif heat <= -0.6:
        reasons.append("✅ 本板块里相对落后/便宜（同行中没怎么涨的一档）")
    else:
        reasons.append("和同板块其它票涨幅差不多")

    # 量价关系（核心维度，单独成行）
    vp_line = f"量价：{vp['state']}——{vp['desc']}"
    if vp["obv_div"]:
        vp_line += "；并且资金在流出(OBV顶背离)，更要警惕"
    q = vp["quality"]
    if not np.isnan(q):
        if q < 0:
            vp_line += "；而且放量的日子反而在跌(派发嫌疑)"
        elif q >= 55:
            vp_line += f"；近60日涨幅约 {min(q,100):.0f}% 来自放量日(扎实)"
        elif q <= 30:
            vp_line += f"；近60日仅约 {q:.0f}% 涨幅靠放量(偏虚)"
    reasons.append(vp_line)

    # 超买
    if not np.isnan(rsi_v):
        if rsi_v >= 72:
            reasons.append(f"短期超买（RSI {rsi_v:.0f}，>70 偏高，追进去容易吃回调）")
        elif rsi_v <= 35:
            reasons.append(f"短期超卖（RSI {rsi_v:.0f}，<35 常是阶段性低点）")

    # ---- 综合判断（量价关系深度参与）----
    weak_trend = (not np.isnan(ma200)) and last < ma200
    overbought = (not np.isnan(rsi_v)) and rsi_v >= 72
    bad_vp = vp["state"] in ("价涨量缩", "价跌量增") or vp["obv_div"]
    good_vp = vp["state"] == "价涨量增"
    healthy_pullback = vp["state"] == "价跌量缩"   # 缩量回调

    if weak_trend:
        light, one = "🔴", "趋势走弱，先别加，等站回200日线再说"
    elif vp["state"] == "价跌量增":
        light, one = "🔴", "放量下跌、抛压重，别接刀，等止跌再看"
    elif heat >= 1.0 or overbought:
        light, one = "🔴", "板块里涨过头/短期超买，别追高，等回调到50日线附近"
    elif vp["state"] == "价涨量缩" or vp["obv_div"]:
        # 即使板块里相对便宜，缩量上涨/资金流出也只能观望，不主动加
        light, one = "🟡", "涨势缺量/资金在流出，先别加，等放量确认或回调到位"
    elif heat <= -0.6 and last > ma50 and (good_vp or healthy_pullback):
        light, one = "🟢", "板块里相对便宜、趋势没坏、且量价健康 —— 可考虑逢低加仓"
    elif healthy_pullback and last > ma50:
        light, one = "🟢", "缩量回调到位、抛压衰竭 —— 趋势没坏可考虑分批低吸"
    elif good_vp and last > ma50 and heat < 1.0:
        light, one = "🟢", "放量上涨、量价齐升，趋势健康 —— 可顺势小幅加"
    elif last > ma50:
        light, one = "🟡", "趋势在，但量价/估值都不算便宜，小仓位或先观望"
    else:
        light, one = "🟡", "回调中、还没站稳，观望为主"
    return light, one, reasons


def sell_advice(m, heat, buy_price, shares):
    """按买入价给卖出/止损建议。返回 (信号灯, 一句话, 关键价位dict)。"""
    last = m["last"]
    pnl = (last / buy_price - 1) * 100
    stop = buy_price * (1 + STOP_LOSS_PCT)
    tp1 = buy_price * (1 + TAKE_PROFIT_1)
    tp2 = buy_price * (1 + TAKE_PROFIT_2)
    ma20 = m["ma20"]

    levels = {"现价": last, "成本": buy_price, "盈亏%": pnl,
              "止损价": stop, "止盈一(卖1/3)": tp1, "止盈二(再卖一部分)": tp2,
              "移动止盈线(20日线)": ma20}

    vp = m["vp"]
    overheated = heat >= 1.0
    # 量价警号：高位缩量上涨 / 资金流出 / 放量下跌 —— 都是该保护利润的信号
    vp_warn = vp["state"] in ("价涨量缩", "价跌量增") or vp["obv_div"]

    if last <= stop:
        light, one = "🔴", f"已跌破止损价 ${stop:.2f}（亏 {pnl:.1f}%）→ 建议止损离场，保护本金"
    elif vp["state"] == "价跌量增" and pnl > 0:
        light, one = "🟠", f"已盈利 {pnl:.1f}% 但出现放量下跌(抛压重) → 建议先卖一半落袋，跌破 ${ma20:.2f}(20日线) 清掉"
    elif last >= tp2:
        light, one = "🟢", f"已大赚 {pnl:.1f}%（超 +30%）→ 建议至少卖一半锁利，剩余跌破20日线 ${ma20:.2f} 再清"
    elif (overheated or vp_warn) and pnl > 0:
        why = "本板块里涨过头" if overheated else "量价转弱(缩量上涨/资金流出)"
        light, one = "🟢", f"已盈利 {pnl:.1f}% 且{why} → 建议先卖一半锁利，剩余设移动止盈（跌破20日线 ${ma20:.2f}）"
    elif last >= tp1:
        light, one = "🟢", f"已盈利 {pnl:.1f}%（超 +15%）→ 建议卖 1/3 锁利，其余继续拿，止损上移到成本价 ${buy_price:.2f}"
    elif pnl >= 0:
        tail = "；不过量价转弱，别恋战" if vp_warn else "（量价仍健康，可拿住）"
        light, one = "🟡", f"小幅盈利 {pnl:.1f}%，未到止盈目标 → 继续拿；跌破 ${stop:.2f} 就止损{tail}"
    else:
        light, one = "🟡", f"暂时浮亏 {pnl:.1f}%，还没破止损 ${stop:.2f} → 按计划拿住；跌破止损价就走，别扛"

    # 量价附注，让你看到为什么这么判
    one += f"\n      量价：{vp['state']}——{vp['desc']}"
    if vp["obv_div"]:
        one += "；资金在净流出(OBV顶背离)"

    if shares and not np.isnan(shares):
        pnl_money = (last - buy_price) * shares
        one += f"\n      当前这笔约 {'+' if pnl_money >= 0 else ''}{pnl_money:,.0f} 美元"
    return light, one, levels


# ============================================================================
# 5) 持仓文件
# ============================================================================
def ensure_positions_file():
    if os.path.exists(POSITIONS_FILE):
        return
    template = (
        "# 在这里填你持有的股票。用 Excel 或记事本打开都行。\n"
        "# 三列：代码(美股), 买入均价, 股数(可留空)。# 开头的行是注释，会被忽略。\n"
        "ticker,buy_price,shares\n"
        "# 下面两行是示例（开头有#=被忽略）。把你真实持仓照这个格式写在下面，去掉#：\n"
        "# NVDA,150.00,10\n"
        "# COHR,80.00,5\n"
    )
    with open(POSITIONS_FILE, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"已生成持仓模板：{POSITIONS_FILE}（请用 Excel 填上你的真实持仓后再跑一次）\n")


def load_positions():
    if not os.path.exists(POSITIONS_FILE):
        return {}
    try:
        df = pd.read_csv(POSITIONS_FILE, comment="#")
    except Exception:
        return {}
    df.columns = [c.strip().lower() for c in df.columns]
    if "ticker" not in df.columns or "buy_price" not in df.columns:
        return {}
    pos = {}
    for _, row in df.iterrows():
        t = str(row["ticker"]).strip().upper()
        if not t or t == "NAN":
            continue
        try:
            bp = float(row["buy_price"])
        except (ValueError, TypeError):
            continue
        sh = np.nan
        if "shares" in df.columns:
            try:
                sh = float(row["shares"])
            except (ValueError, TypeError):
                sh = np.nan
        pos[t] = (bp, sh)
    return pos


# ============================================================================
# 6) 打印报告
# ============================================================================
def name_of(t):
    return f"{NAMES.get(t, t)}({t})"


def sector_of(t):
    for s, ts in WATCHLIST.items():
        if t in ts:
            return s
    return "其它"


def print_report(metrics, heat, positions, as_of):
    lines = []
    out = lines.append   # 收集每一行，最后统一打印 + 存文件

    line = "=" * 64
    out("")
    out(line)
    out(f"  每日盯盘报告　数据截至：{as_of}（开盘前最新可得的收盘价）")
    out(line)

    # ---- A. 我的持仓 ----
    out("")
    out("【一】我的持仓 —— 该拿 / 卖 / 止损？")
    out("")
    held = [t for t in positions if t in metrics]
    if not held:
        out("  （持仓文件 my_positions.csv 里没有可识别的持仓，或这些代码不在下载范围内）")
    for t in held:
        bp, sh = positions[t]
        m = metrics[t]
        light, one, lv = sell_advice(m, heat.get(t, 0.0), bp, sh)
        out(f"  {light} {name_of(t)}　[{sector_of(t)}]")
        out(f"      {one}")
        out(f"      现价 ${lv['现价']:.2f}｜成本 ${lv['成本']:.2f}｜盈亏 {lv['盈亏%']:+.1f}%")
        out(f"      关键价位：止损 ${lv['止损价']:.2f}　|　止盈① ${lv['止盈一(卖1/3)']:.2f}　|　止盈② ${lv['止盈二(再卖一部分)']:.2f}")
        out("")

    # ---- B. 观察名单（按板块，板块内按相对便宜→相对贵排序）----
    out("")
    out("【二】观察名单 —— 现在能不能加仓？（每个板块内部相互比）")
    out("")
    for sector, tickers in WATCHLIST.items():
        members = [t for t in tickers if t in metrics]
        if not members:
            continue
        # 板块内：热度低（相对便宜）排前面
        members.sort(key=lambda x: heat.get(x, 0.0))
        out(f"  ── {sector} ──（从“板块里相对便宜”到“相对涨过头”排序）")
        for t in members:
            m = metrics[t]
            light, one, reasons = add_advice(m, heat.get(t, 0.0))
            hot = heat.get(t, 0.0)
            tag = "🔥相对最热" if hot >= 1.0 else ("💧相对最便宜" if hot <= -0.6 else "·")
            vptag = m["vp"]["state"]
            if m["vp"]["obv_div"]:
                vptag += "+资金流出"
            r1m_s = f"{m['r1m']:+.1f}%" if not np.isnan(m["r1m"]) else "n/a"
            r3m_s = f"{m['r3m']:+.1f}%" if not np.isnan(m["r3m"]) else "n/a(历史短)"
            out(f"    {light} {name_of(t):<16} 现价 ${m['last']:.2f}　近1月 {r1m_s}　近3月 {r3m_s}　[量价:{vptag}]　{tag}")
            out(f"        建议：{one}")
            out(f"        理由：{'；'.join(reasons)}")
        out("")

    out(line)
    out("  说明：本工具只做数据辅助参考，不是投资保证。最终决策结合你的资金、")
    out("        风险承受力和当天盘前/盘后实际报价。'涨过头'仅在同板块内相对比较。")
    out("  改持仓：用 Excel 编辑 my_positions.csv　|　改盯盘股票：编辑 daily_check.py 顶部 WATCHLIST")
    out(line)

    text = "\n".join(lines)
    print(text)
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        # 再按数据日期归档一份到 reports/，历史报告全部保留，方便日后回看/对比
        os.makedirs(REPORTS_DIR, exist_ok=True)
        dated = os.path.join(REPORTS_DIR, f"报告_{as_of}.txt")
        with open(dated, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n（最新报告：{REPORT_FILE}　|　已归档：{dated}）")
    except Exception as e:
        print(f"\n（报告存文件失败，不影响查看：{e}）")


# ============================================================================
# 7) 主流程
# ============================================================================
def main():
    ensure_positions_file()

    all_tickers = [t for ts in WATCHLIST.values() for t in ts]
    frames = download_all(all_tickers, period="1y")

    if frames:
        close, vol, high, low = build_panels(frames)
        try:
            save_cache(close, vol, high, low)
        except Exception as e:
            print(f"  （缓存保存失败，不影响本次：{e}）")
    else:
        print("  本次全部下载失败，尝试读取上次缓存数据...")
        cached = load_cache()
        if cached is None:
            print("  没有可用缓存，退出。请检查网络后重试。")
            sys.exit(1)
        close, vol, high, low = cached

    metrics = compute_metrics(close, vol)
    if not metrics:
        print("  没有足够数据计算指标，退出。")
        sys.exit(1)
    heat = sector_heat(metrics)
    positions = load_positions()
    as_of = close.index[-1].date()
    print_report(metrics, heat, positions, as_of)


if __name__ == "__main__":
    main()
