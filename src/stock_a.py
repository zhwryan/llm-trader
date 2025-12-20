import os
import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))


def stock_basic(list_status: str = "L", exchange: str = "") -> pd.DataFrame:
    return pro.stock_basic(list_status=list_status, exchange=exchange)


def daily(
    ts_code: Optional[str] = None,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:

    def _last_open_date(end_yyyymmdd: str) -> str:
        cal = pro.trade_cal(exchange="", end_date=end_yyyymmdd, is_open=1)
        return cal.iloc[-1]["cal_date"] if not cal.empty else end_yyyymmdd

    df = pro.daily(
        ts_code=ts_code,
        trade_date=trade_date,
        start_date=start_date,
        end_date=end_date,
    )
    if df.empty and trade_date:
        last = _last_open_date(trade_date)
        df = pro.daily(ts_code=ts_code, start_date=last, end_date=last)
    cols = [
        c
        for c in ["open", "close", "high", "low", "vol", "amount", "pct_chg"]
        if c in df.columns
    ]
    return df[cols].rename(columns={"vol": "volume", "amount": "money"})


if __name__ == '__main__':
    stock_list = ["000001.SZ", "600036.SH", "002594.SZ"]
    end = _today_yyyymmdd()
    last = _last_open_date(end)
    rows = []
    for code in stock_list:
        d = daily(ts_code=code, start_date=last, end_date=last)
        if d.empty:
            continue
        r = d[["ts_code", "close", "pct_chg", "volume"]]
        rows.append(r)
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["ts_code", "close", "pct_chg", "volume"])
    df.to_excel("股票最新数据.xlsx", index=False)
    print("导出完成")
