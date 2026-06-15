import yfinance as yf
import pandas as pd

tickers = ["MU", "SNDK", "WDC", "STX", "005930.KS", "000660.KS", "285A.T"]

data = {}
for t in tickers:
    df = yf.download(t, period="1y", interval="1d", auto_adjust=False)
    df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    df.columns = [f"{t}_{c}" for c in df.columns]
    data[t] = df

merged = pd.concat(data.values(), axis=1)

with pd.ExcelWriter("storage_stocks_ohlcv.xlsx") as writer:
    merged.to_excel(writer, sheet_name="OHLCV")

print("Done: storage_stocks_ohlcv.xlsx")