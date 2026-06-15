"""
refresh_status.py — One-shot status report for periodic LS re-analysis.

Run AFTER storage_stock.py (which refreshes the price data), then copy the
output into a Claude Code session along with current after-hours prices and
your open positions. Claude will use this snapshot + your portfolio state
to evaluate whether to hold/trim/exit/open positions.
"""
import re
import numpy as np
import pandas as pd

XLSX = "storage_stocks_ohlcv.xlsx"
TICKERS = ["MU", "SNDK", "WDC", "STX", "005930.KS", "000660.KS", "285A.T"]
NICE = {"MU": "Micron", "SNDK": "SanDisk", "WDC": "WD", "STX": "Seagate",
        "005930.KS": "Samsung", "000660.KS": "Hynix", "285A.T": "Kioxia"}
TICKER_OF = {v: k for k, v in NICE.items()}

# Load price data
raw = pd.read_excel(XLSX, sheet_name="OHLCV")
raw["Date"] = pd.to_datetime(raw["Date"])
raw = raw.set_index("Date").sort_index()
pat = re.compile(r"^(?P<t>[^_]+)_\('(?P<f>[^']+)',")
raw.columns = pd.MultiIndex.from_tuples(
    [(pat.match(c)["t"], pat.match(c)["f"]) for c in raw.columns])
close = raw.xs("Adj Close", level=1, axis=1).ffill().dropna(how="all")
volume = raw.xs("Volume", level=1, axis=1).reindex(close.index)
ret = close.pct_change()
log_ret = np.log(close / close.shift(1))

last_date = close.index[-1].date()
print(f"==== Storage/Memory LS Status Report ====")
print(f"As of (last trading day): {last_date}")
print(f"Universe: {', '.join(NICE.values())}")
print()

# -------- 1. Performance --------
print("[1] Recent Performance (% return, local currency)")
print(f"  {'Stock':<10} {'1W':>7} {'1M':>7} {'3M':>7} {'YTD':>7} {'Last px':>14}")
for t in TICKERS:
    px = close[t].iloc[-1]
    p1w = (close[t].iloc[-1] / close[t].iloc[-6] - 1) * 100
    p1m = (close[t].iloc[-1] / close[t].iloc[-22] - 1) * 100
    p3m = (close[t].iloc[-1] / close[t].iloc[-64] - 1) * 100
    pY  = (close[t].iloc[-1] / close[t].iloc[0]   - 1) * 100
    print(f"  {NICE[t]:<10} {p1w:+7.1f} {p1m:+7.1f} {p3m:+7.1f} {pY:+7.1f} {px:>14.2f}")
print()

# -------- 2. Mispricing Signal --------
W = pd.Series({"HBM": 1.0, "DRAM_ex": 0.8, "NAND_Ent": 0.85,
               "NAND_Cons": 0.4, "HDD": 0.7, "Other": 0.1})
MIX = pd.DataFrame.from_dict({
    "MU":        {"HBM": 18, "DRAM_ex": 50, "NAND_Ent": 25, "NAND_Cons": 7,  "HDD": 0,   "Other": 0},
    "SNDK":      {"HBM": 0,  "DRAM_ex": 0,  "NAND_Ent": 50, "NAND_Cons": 50, "HDD": 0,   "Other": 0},
    "WDC":       {"HBM": 0,  "DRAM_ex": 0,  "NAND_Ent": 0,  "NAND_Cons": 0,  "HDD": 100, "Other": 0},
    "STX":       {"HBM": 0,  "DRAM_ex": 0,  "NAND_Ent": 5,  "NAND_Cons": 0,  "HDD": 95,  "Other": 0},
    "005930.KS": {"HBM": 4,  "DRAM_ex": 9,  "NAND_Ent": 9,  "NAND_Cons": 9,  "HDD": 0,   "Other": 69},
    "000660.KS": {"HBM": 38, "DRAM_ex": 30, "NAND_Ent": 22, "NAND_Cons": 8,  "HDD": 0,   "Other": 2},
    "285A.T":    {"HBM": 0,  "DRAM_ex": 0,  "NAND_Ent": 50, "NAND_Cons": 50, "HDD": 0,   "Other": 0},
}, orient="index")
ai_score = (MIX * W).sum(axis=1)
ma50 = close.rolling(50).mean()
ext50 = (close.iloc[-1] / ma50.iloc[-1] - 1) * 100
mispr = ext50 - 0.6 * ai_score
print("[2] Mispricing Signal (new weights: HBM 1.0 / DRAM 0.8 / NAND-Ent 0.85 / NAND-Cons 0.4 / HDD 0.7)")
print(f"  Negative = under-priced (BUY candidate), Positive = over-extended (SHORT candidate)")
print(f"  {'Stock':<10} {'AI score':>10} {'Ext MA50':>10} {'Mispr':>10}")
order = mispr.sort_values().index
for t in order:
    print(f"  {NICE[t]:<10} {ai_score[t]:10.1f} {ext50[t]:+10.1f} {mispr[t]:+10.1f}")
print()

# -------- 3. Pair z-scores (USD-flat assumption) --------
# Assume FX-stable for status report. User provides current FX in Claude session
# for real-time precision. Use the same constant FX as previously discussed:
KRW_per_USD = 1 / 0.000655  # historic baseline; tell Claude if FX has moved >1%

def usd_series(t):
    if t in ["000660.KS", "005930.KS"]:
        return close[t] / KRW_per_USD
    return close[t]

PAIRS = [
    # USD-tradable pairs (both legs in USD-denominated futures/instruments)
    ("Hynix",   "Micron",  "000660.KS", "MU"),
    ("Hynix",   "SNDK",    "000660.KS", "SNDK"),
    ("Hynix",   "WDC",     "000660.KS", "WDC"),
    ("Samsung", "Micron",  "005930.KS", "MU"),
    ("Samsung", "SNDK",    "005930.KS", "SNDK"),
    ("Samsung", "WDC",     "005930.KS", "WDC"),
    ("Samsung", "Hynix",   "005930.KS", "000660.KS"),
    ("WDC",     "SNDK",    "WDC",       "SNDK"),
    ("WDC",     "Micron",  "WDC",       "MU"),
    ("Micron",  "SNDK",    "MU",        "SNDK"),
]

print("[3] Pair Z-scores (60d rolling, USD-flat at baseline FX)")
print(f"  Flag '!!' = extreme (|z|>=1.8σ), single-pair entry-worthy")
print(f"  {'Long':<8} / {'Short':<8} {'Z':>8} {'Half-life':>10} {'1σ in %':>10} {'Flag':>6}")
for la, sa, ta, tb in PAIRS:
    ratio = (usd_series(ta) / usd_series(tb)).dropna()
    if len(ratio) < 60:
        continue
    mu60 = ratio.rolling(60).mean().iloc[-1]
    sd60 = ratio.rolling(60).std().iloc[-1]
    z = (ratio.iloc[-1] - mu60) / sd60
    # half-life of z (AR1 decay)
    zser = (ratio - ratio.rolling(60).mean()) / ratio.rolling(60).std()
    zc = zser.dropna()
    phi = np.corrcoef(zc.values[:-1], zc.values[1:])[0, 1] if len(zc) > 2 else np.nan
    hl = np.log(0.5) / np.log(phi) if 0 < phi < 1 else np.inf
    sigma_pct = sd60 / mu60 * 100
    flag = "  !!" if abs(z) >= 1.8 else ("  *" if abs(z) >= 1.4 else "")
    print(f"  {la:<8} / {sa:<8} {z:+8.2f} {hl:10.1f} {sigma_pct:10.1f} {flag:>6}")
print()

# -------- 4. Volume Confirmation Quality --------
print("[4] Volume Confirmation Quality (last 90d)")
print(f"  Higher = rally driven by real participation; <30% = mostly drift")
print(f"  {'Stock':<10} {'Quality':>10} {'90d ret %':>12}")
for t in TICKERS:
    lr = log_ret[t].iloc[-90:].dropna()
    v = volume[t].iloc[-90:].reindex(lr.index)
    high = v > v.rolling(20).mean()
    total_log = lr.sum()
    if total_log != 0:
        q = lr[high].sum() / total_log * 100
    else:
        q = np.nan
    ret_90 = (np.exp(total_log) - 1) * 100
    print(f"  {NICE[t]:<10} {q:9.0f}% {ret_90:+11.1f}")
print()

# -------- 5. Recent Volume Trend (5d vs 20d avg) --------
print("[5] Recent Volume Trend (5d avg vs 20d avg, %)")
print(f"  Negative = volume drying up (often precedes reversal)")
for t in TICKERS:
    v5 = volume[t].iloc[-5:].mean()
    v20 = volume[t].iloc[-20:].mean()
    if v20:
        chg = (v5 / v20 - 1) * 100
    else:
        chg = np.nan
    arrow = "↑" if chg > 10 else "↓" if chg < -10 else "→"
    print(f"  {NICE[t]:<10} {chg:+7.1f}%  {arrow}")
print()

# -------- 6. Quick narrative read --------
print("[6] Narrative Heat Map (3M relative performance ordering)")
perf_3m = {t: close[t].iloc[-1] / close[t].iloc[-64] - 1 for t in TICKERS}
order = sorted(perf_3m.items(), key=lambda x: -x[1])
for t, p in order:
    seg = "HBM" if t == "000660.KS" else "HBM/DRAM" if t in ["MU", "005930.KS"] else \
          "pure NAND" if t in ["SNDK", "285A.T"] else "HDD"
    bar = "█" * max(0, int(p * 20))
    print(f"  {NICE[t]:<10} {p*100:+6.1f}%  [{seg}]  {bar}")
print()

print(f"==== End of report. ====")
print(f"Copy this entire output into Claude with:")
print(f"  - current after-hours USD prices (if differ from last close)")
print(f"  - current FX (KRW/USD) if changed >0.5% from 0.000655")
print(f"  - your open positions: pair / entry prices / days held / current PnL")
print(f"  - any instruments NOT tradable in your account")
