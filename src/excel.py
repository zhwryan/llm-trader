import os
import pandas as pd
import tushare as ts
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TS_TOKEN")
if not token:
    raise RuntimeError("缺少TS_TOKEN，请在.env中配置")
ts.set_token(token)
pro = ts.pro_api()

def _today_yyyymmdd() -> str:
    from datetime import datetime
    return datetime.today().strftime("%Y%m%d")

def _last_open_date(end_yyyymmdd: str) -> str:
    cal = pro.trade_cal(exchange="", end_date=end_yyyymmdd, is_open=1)
    return cal.iloc[-1]["cal_date"] if not cal.empty else end_yyyymmdd

stock_list = ["000001.SZ", "600036.SH", "002594.SZ"]
end = _today_yyyymmdd()
last = _last_open_date(end)
rows = []
for code in stock_list:
    d = pro.daily(ts_code=code, start_date=last, end_date=last)
    if d.empty:
        continue
    r = d[["ts_code", "close", "pct_chg", "vol"]].rename(columns={"vol": "volume"})
    rows.append(r)
df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["ts_code", "close", "pct_chg", "volume"])
df.to_excel("股票最新数据.xlsx", index=False)
print("导出完成")
