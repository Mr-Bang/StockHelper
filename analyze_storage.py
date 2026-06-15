"""
Storage / memory stocks horizontal analysis.

Hypothesis under test:
  - SNDK has been the leader, but rising on declining volume (suspicious).
  - Some names may be overextended and due for a pullback.

Inputs : storage_stocks_ohlcv.xlsx  (saved by storage_stock.py)
Outputs: PNG charts + a printed summary table.
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

XLSX = "storage_stocks_ohlcv.xlsx"
TICKERS = ["MU", "SNDK", "WDC", "STX", "005930.KS", "000660.KS", "285A.T"]
NICE = {
    "MU": "Micron",
    "SNDK": "SanDisk",
    "WDC": "WD",
    "STX": "Seagate",
    "005930.KS": "Samsung",
    "000660.KS": "SK Hynix",
    "285A.T": "Kioxia",
}

# ---------- load & reshape ------------------------------------------------
raw = pd.read_excel(XLSX, sheet_name="OHLCV")
raw["Date"] = pd.to_datetime(raw["Date"])
raw = raw.set_index("Date").sort_index()

# column names look like:  MU_('Open', 'MU')   -> turn into (ticker, field)
pat = re.compile(r"^(?P<tkr>[^_]+)_\('(?P<field>[^']+)',")
tuples = []
for c in raw.columns:
    m = pat.match(c)
    tuples.append((m["tkr"], m["field"]))
raw.columns = pd.MultiIndex.from_tuples(tuples, names=["ticker", "field"])

close = raw.xs("Adj Close", level="field", axis=1)
volume = raw.xs("Volume", level="field", axis=1)
openp = raw.xs("Open", level="field", axis=1)

# drop rows where every ticker is NaN (holidays in one market vs another)
close = close.ffill().dropna(how="all")
volume = volume.reindex(close.index)

# ---------- core metrics --------------------------------------------------
ret = close.pct_change()
log_ret = np.log(close / close.shift(1))

def perf(days):
    return close.iloc[-1] / close.iloc[-1 - days] - 1

perf_tbl = pd.DataFrame({
    "1W":  perf(5),
    "1M":  perf(21),
    "3M":  perf(63),
    "6M":  perf(126),
    "1Y":  close.iloc[-1] / close.iloc[0] - 1,
}).loc[TICKERS]

# moving averages & extension
ma20 = close.rolling(20).mean()
ma50 = close.rolling(50).mean()
ma200 = close.rolling(200).mean()
ext20  = close.iloc[-1] / ma20.iloc[-1] - 1
ext50  = close.iloc[-1] / ma50.iloc[-1] - 1
ext200 = close.iloc[-1] / ma200.iloc[-1] - 1

# RSI (Wilder, 14)
def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / dn
    return 100 - 100 / (1 + rs)

rsi14 = close.apply(rsi)

# OBV
def obv(c, v):
    sign = np.sign(c.diff().fillna(0))
    return (sign * v.fillna(0)).cumsum()

obv_df = pd.DataFrame({t: obv(close[t], volume[t]) for t in TICKERS})

# Volume on up-days vs down-days (last 20 sessions): a *real* up-trend
# should print HIGHER volume on green days than on red days.
def up_dn_vol_ratio(t, win=20):
    sl = slice(-win, None)
    r = ret[t].iloc[sl]
    v = volume[t].iloc[sl]
    up_v = v[r > 0].mean()
    dn_v = v[r < 0].mean()
    if not dn_v or np.isnan(dn_v):
        return np.nan
    return up_v / dn_v

vol_quality_20 = {t: up_dn_vol_ratio(t, 20) for t in TICKERS}
vol_quality_60 = {t: up_dn_vol_ratio(t, 60) for t in TICKERS}

# Volume trend during the recent rally: regress log-volume on time
# over the last 20 sessions AND check if price went up over the same window.
def vol_slope(t, win=20):
    v = np.log(volume[t].iloc[-win:].replace(0, np.nan)).dropna()
    if len(v) < 5:
        return np.nan
    x = np.arange(len(v))
    slope = np.polyfit(x, v.values, 1)[0]
    return slope  # log-vol change per day

vol_slope_20 = {t: vol_slope(t, 20) for t in TICKERS}
price_chg_20 = {t: close[t].iloc[-1] / close[t].iloc[-21] - 1 for t in TICKERS}

# Price-Volume divergence flag: price up >5% over 20d AND volume slope < 0
divergence = {
    t: (price_chg_20[t] > 0.05) and (vol_slope_20[t] < 0) for t in TICKERS
}

# 20-day realized volatility (annualised)
vol_ann = log_ret.rolling(20).std().iloc[-1] * np.sqrt(252)

# ---------- summary table -------------------------------------------------
summary = pd.DataFrame({
    "1M %":          (perf_tbl["1M"] * 100).round(1),
    "3M %":          (perf_tbl["3M"] * 100).round(1),
    "1Y %":          (perf_tbl["1Y"] * 100).round(1),
    "ext vs MA20 %": (ext20 * 100).round(1),
    "ext vs MA50 %": (ext50 * 100).round(1),
    "ext vs MA200 %":(ext200 * 100).round(1),
    "RSI14":         rsi14.iloc[-1].round(1),
    "Vol(up/dn) 20d":pd.Series(vol_quality_20).round(2),
    "Vol(up/dn) 60d":pd.Series(vol_quality_60).round(2),
    "Vol slope 20d": pd.Series(vol_slope_20).round(3),
    "Price 20d %":   (pd.Series(price_chg_20) * 100).round(1),
    "Divergent?":    pd.Series(divergence),
    "RealVol 20d":   (vol_ann * 100).round(1),
}).loc[TICKERS]
summary.index = [NICE[t] for t in summary.index]

print("\n=== Storage stocks – snapshot as of",
      close.index[-1].date(), "===\n")
print(summary.to_string())
summary.to_csv("storage_summary.csv")

# correlation of daily returns (last 63 sessions)
corr = ret.iloc[-63:][TICKERS].corr()
corr.index = [NICE[t] for t in corr.index]
corr.columns = [NICE[t] for t in corr.columns]
print("\n--- 63-day return correlation ---")
print(corr.round(2).to_string())
corr.to_csv("storage_corr_63d.csv")

# ---------- charts --------------------------------------------------------
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True,
                     "grid.alpha": 0.3, "font.size": 9})

# 1. Rebased price (last 6M) -----------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
window = close.iloc[-126:]
rebased = window / window.iloc[0] * 100
for t in TICKERS:
    ax.plot(rebased.index, rebased[t], label=NICE[t], linewidth=1.6)
ax.set_title("Storage / memory – rebased to 100 (last ~6 months)")
ax.set_ylabel("Index (start=100)")
ax.legend(ncol=4, fontsize=8)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig("chart1_rebased_6m.png")
plt.close(fig)

# 2. SNDK – price + volume + 20-day avg volume, last 90 sessions -----------
fig, (axp, axv) = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                               gridspec_kw={"height_ratios": [2, 1]})
w = slice(-90, None)
axp.plot(close.index[w], close["SNDK"].iloc[w], color="C1", linewidth=1.6)
axp.plot(close.index[w], ma20["SNDK"].iloc[w],  color="grey", lw=1, ls="--",
         label="MA20")
axp.plot(close.index[w], ma50["SNDK"].iloc[w],  color="black", lw=1, ls=":",
         label="MA50")
axp.set_title("SNDK – price, with MA20/MA50  (last ~90 sessions)")
axp.legend(fontsize=8)

v20 = volume["SNDK"].rolling(20).mean()
axv.bar(volume.index[w], volume["SNDK"].iloc[w], width=1.0, color="C0",
        alpha=0.6, label="Volume")
axv.plot(volume.index[w], v20.iloc[w], color="red", lw=1.4,
         label="20d avg volume")
axv.set_ylabel("Shares")
axv.legend(fontsize=8)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig("chart2_sndk_price_volume.png")
plt.close(fig)

# 3. Up-day vs down-day volume ratio (last 20 sessions) --------------------
fig, ax = plt.subplots(figsize=(8, 4.5))
labels = [NICE[t] for t in TICKERS]
v20s = [vol_quality_20[t] for t in TICKERS]
v60s = [vol_quality_60[t] for t in TICKERS]
x = np.arange(len(labels))
ax.bar(x - 0.2, v20s, width=0.4, label="last 20d", color="C3")
ax.bar(x + 0.2, v60s, width=0.4, label="last 60d", color="C0")
ax.axhline(1.0, color="black", lw=1)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=15)
ax.set_ylabel("Avg up-day volume / avg down-day volume")
ax.set_title("Volume quality on rallies  (>1 = healthy, <1 = suspicious)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig("chart3_volume_quality.png")
plt.close(fig)

# 4. Extension vs MA50 (overheat gauge) ------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5))
ext = (ext50.loc[TICKERS] * 100).values
colors = ["C3" if v > 15 else "C2" if v < 0 else "C0" for v in ext]
ax.barh([NICE[t] for t in TICKERS], ext, color=colors)
ax.axvline(0, color="black", lw=1)
ax.axvline(15, color="red", lw=1, ls="--", label="+15% (stretched)")
ax.set_xlabel("Current price vs 50-day MA, %")
ax.set_title("How far price is sitting above its 50-day MA")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig("chart4_extension_ma50.png")
plt.close(fig)

# 5. OBV vs price for SNDK (divergence visual) -----------------------------
fig, (axp, axo) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
w = slice(-90, None)
axp.plot(close.index[w], close["SNDK"].iloc[w], color="C1", lw=1.6)
axp.set_title("SNDK – price vs OBV (last ~90 sessions). "
              "OBV failing to follow new price highs = bearish divergence.")
axp.set_ylabel("Price")
axo.plot(obv_df.index[w], obv_df["SNDK"].iloc[w], color="C2", lw=1.6)
axo.set_ylabel("OBV (cum signed volume)")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig("chart5_sndk_obv.png")
plt.close(fig)

# 6. RSI snapshot ----------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5))
vals = rsi14.iloc[-1].loc[TICKERS].values
labels = [NICE[t] for t in TICKERS]
colors = ["C3" if v >= 70 else "C2" if v <= 30 else "C0" for v in vals]
ax.barh(labels, vals, color=colors)
ax.axvline(70, color="red", ls="--", lw=1, label="overbought 70")
ax.axvline(30, color="green", ls="--", lw=1, label="oversold 30")
ax.set_xlim(0, 100)
ax.set_xlabel("RSI(14)")
ax.set_title("Current RSI(14)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig("chart6_rsi.png")
plt.close(fig)

# 7. 63-day return correlation heatmap -------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 5.5))
im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-0.2, vmax=1)
ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=35,
                                                    ha="right")
ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.index)
for i in range(len(corr)):
    for j in range(len(corr)):
        ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center",
                fontsize=8, color="black")
ax.set_title("Daily-return correlation, last 63 sessions")
fig.colorbar(im, ax=ax, fraction=0.046)
fig.tight_layout()
fig.savefig("chart7_corr.png")
plt.close(fig)

print("\nCharts written:")
for i in range(1, 8):
    print(f"  chart{i}_*.png")
