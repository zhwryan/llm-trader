import os
import sys
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))


def stock_basic(list_status: str = "L", exchange: str = "") -> pd.DataFrame:
    return pro.stock_basic(list_status=list_status, exchange=exchange)


def get_code_by_name(name: str) -> Optional[tuple[str, str]]:
    """
    根据名称模糊查找股票代码
    Returns: (ts_code, symbol) e.g. ('600519.SH', '600519')
    """
    try:
        df = stock_basic()
        # 精确匹配
        match = df[df['name'] == name]
        if not match.empty:
            return match.iloc[0]['ts_code'], match.iloc[0]['symbol']

        # 模糊匹配
        match = df[df['name'].str.contains(name)]
        if not match.empty:
            # 返回第一个匹配项
            print(
                f"找到多个匹配项，使用第一个: {match.iloc[0]['name']} ({match.iloc[0]['ts_code']})"
            )
            return match.iloc[0]['ts_code'], match.iloc[0]['symbol']

        print(f"未找到名称包含 '{name}' 的股票")
        return None
    except Exception as e:
        print(f"搜索股票失败: {e}")
        return None


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

    # 确保所需列存在
    if df.empty:
        return df

    cols = [
        c for c in [
            "trade_date", "open", "close", "high", "low", "vol", "amount",
            "pct_chg"
        ] if c in df.columns
    ]
    return df[cols].rename(columns={"vol": "volume", "amount": "money"})


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m src.stock_a <command> [args]")
        print("Commands:")
        print("  search <name>  - Search stock code by name")
        print("  data <code>    - Get recent daily data for code")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        if len(sys.argv) < 3:
            print("Please provide a stock name")
            sys.exit(1)
        name = sys.argv[2]
        result = get_code_by_name(name)
        if result:
            print(f"FOUND: {result[0]} {result[1]}")
        else:
            sys.exit(1)

    elif cmd == "data":
        if len(sys.argv) < 3:
            print("Please provide a stock code (ts_code)")
            sys.exit(1)
        code = sys.argv[2]
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        df = daily(ts_code=code, start_date=start_date, end_date=end_date)
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("No data found")

    else:
        print(f"Unknown command: {cmd}")
