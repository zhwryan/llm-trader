import os
import pandas as pd
import tushare as ts
from dotenv import load_dotenv

load_dotenv()

ts.set_token(os.getenv("TUSHARE_TOKEN"))
pro = ts.pro_api()


def hk_daily(
    ts_code: str | None = None,
    trade_date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    df = pro.hk_daily(
        ts_code=ts_code,
        trade_date=trade_date,
        start_date=start_date,
        end_date=end_date,
    )
    cols = [
        c
        for c in ["open", "close", "high", "low", "vol", "amount", "pct_chg"]
        if c in df.columns
    ]
    return df[cols].rename(columns={"vol": "volume", "amount": "money"})


stock_code = "1208.HK"
ds = "20250819"
df = hk_daily(stock_code, ds)
print(df)
